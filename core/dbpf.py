"""
==============================================================================
Crazy The Sims 4 Project - Core DBPF 2.x Engine
==============================================================================
Pure Python parser, reader, extractor, and builder for The Sims 4 .package files
(DBPF 2.0 & 2.1) and String Tables (STBL v5).
"""

import os
import struct
import zlib
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple, Union

# Known Sims 4 Resource Types
TYPE_CASP = 0x034AEECB          # CAS Part (Clothes, Hair, Makeup, Accessories)
TYPE_GEOM = 0x015A1849          # CAS Geometry (3D Mesh)
TYPE_MODEL = 0x01661233         # Object 3D Model
TYPE_MODEL_LOD = 0x01D10F34     # Object 3D Model LOD
TYPE_OBJD = 0xC0DB5AE7          # Object Definition
TYPE_OBJ_CATALOG = 0x319E4F1D   # Build/Buy Catalog
TYPE_RLE2 = 0x3453CF95          # Texture (RLE2)
TYPE_RLES = 0xBA856C78          # Texture (RLES)
TYPE_DST = 0x00B2D882           # Texture (DST / DXT)
TYPE_PNG = 0x2F7D0004           # Standard PNG Image
TYPE_STBL = 0x220557DA          # String Table (Localization strings)
TYPE_RIG = 0x8EAF13DE           # Skeleton / Rig
TYPE_BONE_DELTA = 0x0355E0A6    # CAS Slider / Bone Delta
TYPE_CLIP = 0x6B20C4F3          # Animation Clip
TYPE_TUNING_XML = 0x6017E896    # XML Tuning
TYPE_SIMDATA = 0x545AC67A       # Binary SimData Tuning

RESOURCE_TYPE_NAMES = {
    TYPE_CASP: "CAS Part (Baju/Rambut/Aksesori)",
    TYPE_GEOM: "CAS 3D Mesh (GEOM)",
    TYPE_MODEL: "Object 3D Model",
    TYPE_MODEL_LOD: "Object 3D Model LOD",
    TYPE_OBJD: "Object Definition",
    TYPE_OBJ_CATALOG: "Build/Buy Catalog",
    TYPE_RLE2: "Texture (RLE2)",
    TYPE_RLES: "Texture (RLES)",
    TYPE_DST: "Texture (DST/DXT)",
    TYPE_PNG: "PNG Image Thumbnail",
    TYPE_STBL: "String Table (STBL)",
    TYPE_RIG: "Rig / Skeleton",
    TYPE_BONE_DELTA: "CAS Slider (Bone Delta)",
    TYPE_CLIP: "Animation Clip",
    TYPE_TUNING_XML: "XML Tuning",
    TYPE_SIMDATA: "SimData",
}


def get_resource_type_name(res_type: int) -> str:
    """Returns a friendly display name for a resource type ID."""
    return RESOURCE_TYPE_NAMES.get(res_type, f"Unknown (0x{res_type:08X})")


class DBPFResource:
    """Represents a single resource entry inside a The Sims 4 .package file."""

    def __init__(
        self,
        res_type: int,
        res_group: int,
        instance_id: int,
        data: bytes = b"",
        compressed: bool = True,
        offset: int = 0,
        mem_size: int = 0
    ):
        self.res_type: int = res_type
        self.res_group: int = res_group
        self.instance_id: int = instance_id
        self.data: bytes = data
        self.compressed: bool = compressed
        self.offset: int = offset
        self.mem_size: int = mem_size or len(data)

    @property
    def tgi(self) -> str:
        return f"0x{self.res_type:08X}:0x{self.res_group:08X}:0x{self.instance_id:016X}"

    @property
    def size(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"<DBPFResource TGI={self.tgi} Size={len(self.data)} bytes>"


class DBPFPackage:
    """
    Complete DBPF 2.0 / 2.1 Reader, Editor, and Builder.
    Reads index entries (with or without compression flags), extracts raw/decompressed
    resource bytes, and saves fully compliant Sims 4 .package files.
    """

    HEADER_SIZE = 96
    DBPF_MAGIC = b"DBPF"
    COMPRESSION_ZLIB = 0x5A42

    def __init__(self, filepath: Optional[str] = None):
        self.filepath: Optional[str] = filepath
        self.resources: List[DBPFResource] = []
        if filepath and os.path.exists(filepath):
            self.load(filepath)

    def load(self, filepath: str):
        """Loads and indexes resources from a .package file."""
        self.filepath = filepath
        self.resources.clear()

        size = os.path.getsize(filepath)
        if size < self.HEADER_SIZE:
            raise ValueError(f"File too small ({size} bytes) to be a valid DBPF package.")

        with open(filepath, "rb") as f:
            header = f.read(self.HEADER_SIZE)
            if len(header) < self.HEADER_SIZE:
                raise ValueError("Could not read full DBPF header.")

            magic = header[:4]
            if magic != self.DBPF_MAGIC:
                raise ValueError(f"Invalid magic header: {magic!r}. Expected {self.DBPF_MAGIC!r}.")

            major = struct.unpack_from("<I", header, 4)[0]
            if major != 2:
                raise ValueError(f"Unsupported DBPF major version: {major}. Expected 2.")

            entry_count = struct.unpack_from("<I", header, 36)[0]
            index_size = struct.unpack_from("<I", header, 44)[0]
            index_pos = struct.unpack_from("<Q", header, 64)[0]

            if entry_count == 0:
                return

            if index_pos < self.HEADER_SIZE or index_pos >= size:
                raise ValueError(f"Corrupted package: Index offset 0x{index_pos:X} outside valid file range.")

            f.seek(index_pos)
            index_data = f.read(index_size if index_size > 0 else (size - index_pos))

            if len(index_data) < 4:
                raise ValueError("Corrupted package: Truncated index data.")

            flags = struct.unpack_from("<I", index_data, 0)[0]
            pos = 4
            c_type = c_group = c_hi = 0

            if flags & 1:
                c_type = struct.unpack_from("<I", index_data, pos)[0]
                pos += 4
            if flags & 2:
                c_group = struct.unpack_from("<I", index_data, pos)[0]
                pos += 4
            if flags & 4:
                c_hi = struct.unpack_from("<I", index_data, pos)[0]
                pos += 4

            fmt = "<"
            fmt += "" if flags & 1 else "I"  # type
            fmt += "" if flags & 2 else "I"  # group
            fmt += "" if flags & 4 else "I"  # instance hi
            fmt += "I"                       # instance lo
            fmt += "IIIHH"                   # offset, size, memsize, comp, committed
            rec_size = struct.calcsize(fmt)

            if len(index_data) - pos < rec_size * entry_count:
                # Fallback for standard 32-byte non-flagged records if flags was zero or corrupt
                if len(index_data) - 4 >= 32 * entry_count:
                    pos = 4
                    flags = 0
                    fmt = "<IIIIIIIHH"
                    rec_size = 32
                else:
                    raise ValueError("Corrupted package: Index buffer smaller than declared entries.")

            for vals in struct.iter_unpack(fmt, index_data[pos : pos + rec_size * entry_count]):
                i = 0
                if flags & 1:
                    t = c_type
                else:
                    t = vals[i]
                    i += 1

                if flags & 2:
                    g = c_group
                else:
                    g = vals[i]
                    i += 1

                if flags & 4:
                    hi = c_hi
                else:
                    hi = vals[i]
                    i += 1

                lo = vals[i]
                inst = (hi << 32) | lo

                offset = vals[i + 1]
                size_flag = vals[i + 2]
                memsize = vals[i + 3]
                comp_flag = vals[i + 4]

                is_compressed = bool(size_flag & 0x80000000) or (comp_flag != 0)
                stored_size = size_flag & 0x7FFFFFFF

                # Read raw data
                f.seek(offset)
                raw_data = f.read(stored_size)

                decompressed_data = raw_data
                if is_compressed and raw_data:
                    try:
                        decompressed_data = zlib.decompress(raw_data)
                    except Exception:
                        # Fallback: maybe raw or non-standard compression
                        decompressed_data = raw_data

                res = DBPFResource(
                    res_type=t,
                    res_group=g,
                    instance_id=inst,
                    data=decompressed_data,
                    compressed=is_compressed,
                    offset=offset,
                    mem_size=memsize or len(decompressed_data)
                )
                self.resources.append(res)

    def add_resource(self, resource: DBPFResource):
        """Adds a resource or replaces an existing resource with the same TGI."""
        for i, r in enumerate(self.resources):
            if r.res_type == resource.res_type and r.res_group == resource.res_group and r.instance_id == resource.instance_id:
                self.resources[i] = resource
                return
        self.resources.append(resource)

    def remove_resource(self, res_type: int, res_group: int, instance_id: int) -> bool:
        """Removes a resource matching the specified TGI. Returns True if removed."""
        init_len = len(self.resources)
        self.resources = [
            r for r in self.resources
            if not (r.res_type == res_type and r.res_group == res_group and r.instance_id == instance_id)
        ]
        return len(self.resources) < init_len

    def find_resources(
        self,
        res_type: Optional[int] = None,
        res_group: Optional[int] = None,
        instance_id: Optional[int] = None
    ) -> List[DBPFResource]:
        """Finds all resources matching the given TGI criteria."""
        res = self.resources
        if res_type is not None:
            res = [r for r in res if r.res_type == res_type]
        if res_group is not None:
            res = [r for r in res if r.res_group == res_group]
        if instance_id is not None:
            res = [r for r in res if r.instance_id == instance_id]
        return res

    def find_by_type(self, res_type: int) -> List[DBPFResource]:
        """Finds all resources matching the given resource type."""
        return self.find_resources(res_type=res_type)

    def get_resource_data(self, res_type: int, res_group: int, instance_id: int) -> Optional[bytes]:
        """Gets the uncompressed data for a specific TGI, or None if not found."""
        matches = self.find_resources(res_type, res_group, instance_id)
        return matches[0].data if matches else None

    def save(self, output_path: str):
        """Writes all resources into a valid, optimized The Sims 4 DBPF 2.0 .package file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        entry_count = len(self.resources)
        body_bytes = bytearray()
        index_records = []
        current_offset = self.HEADER_SIZE

        for res in self.resources:
            uncompressed_size = len(res.data)
            if res.compressed and uncompressed_size > 0:
                compressed_data = zlib.compress(res.data, level=6)
                stored_data = compressed_data
                is_comp = True
                stored_size = len(compressed_data)
            else:
                stored_data = res.data
                is_comp = False
                stored_size = uncompressed_size

            body_bytes.extend(stored_data)

            inst_high = (res.instance_id >> 32) & 0xFFFFFFFF
            inst_low = res.instance_id & 0xFFFFFFFF
            size_flag = stored_size | (0x80000000 if is_comp else 0)
            comp_flag = 0xFFFF if is_comp else 0x0000

            index_records.append((
                res.res_type,
                res.res_group,
                inst_high,
                inst_low,
                current_offset,
                size_flag,
                uncompressed_size,
                comp_flag,
                1  # Committed
            ))
            current_offset += stored_size

        index_offset = current_offset
        index_size = 4 + (entry_count * 32)

        # 96-byte DBPF Header
        header = bytearray(self.HEADER_SIZE)
        header[0:4] = self.DBPF_MAGIC
        struct.pack_into("<I", header, 0x04, 2)            # Major Version 2
        struct.pack_into("<I", header, 0x08, 0)            # Minor Version 0
        struct.pack_into("<I", header, 0x24, entry_count)   # Entry Count
        struct.pack_into("<I", header, 0x2C, index_size)    # Index Size
        struct.pack_into("<I", header, 0x3C, 3)             # Index Version
        struct.pack_into("<Q", header, 0x40, index_offset)  # Index Offset (64-bit)

        # Index Table: flags = 0 (all fields explicit)
        index_bytes = bytearray()
        index_bytes.extend(struct.pack("<I", 0))
        for rec in index_records:
            index_bytes.extend(struct.pack(
                "<IIIIIIIHH",
                rec[0], rec[1], rec[2], rec[3], rec[4], rec[5], rec[6], rec[7], rec[8]
            ))

        with open(output_path, "wb") as f:
            f.write(header)
            f.write(body_bytes)
            f.write(index_bytes)

    def save_atomic(self, output_path: str):
        """Saves package atomically via a temporary file to avoid file corruption on interruption."""
        dir_name = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(dir_name, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp_pkg")
        os.close(fd)
        try:
            self.save(tmp_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            shutil.move(tmp_path, output_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


# ============================================================================
# STRING TABLE (STBL v5) PARSER AND BUILDER
# ============================================================================
class STBL:
    """Sims 4 String Table parser and serializer."""

    @staticmethod
    def parse(data: bytes) -> List[Tuple[int, str]]:
        """Parses STBL binary data into a list of (key_hash, string_text)."""
        if not data or len(data) < 17:
            return []

        entries: List[Tuple[int, str]] = []

        # Standard STBL v5
        if data[:4] == b"STBL":
            try:
                count = struct.unpack_from("<I", data, 7)[0]
                if count == 0:
                    return []
            except Exception:
                count = -1

            for offset_start in (17, 21):
                try:
                    if 0 < count < 100000:
                        pos = offset_start
                        parsed = []
                        for _ in range(count):
                            if pos + 7 > len(data):
                                break
                            key_hash = struct.unpack_from("<I", data, pos)[0]
                            # flags = data[pos + 4]
                            s_len = struct.unpack_from("<H", data, pos + 5)[0]
                            pos += 7
                            if pos + s_len > len(data):
                                break
                            text = data[pos : pos + s_len].decode("utf-8", errors="replace")
                            parsed.append((key_hash, text))
                            pos += s_len
                        if len(parsed) == count:
                            return parsed
                        if len(parsed) > len(entries):
                            entries = parsed
                except Exception:
                    pass

        if entries:
            return entries

        # Fallback: Extract UTF-8 strings
        import re
        try:
            matches = re.finditer(rb"[\x20-\x7E\xC2-\xF4][\x20-\x7E\x80-\xBF]{2,200}", data)
            for m in matches:
                try:
                    txt = m.group(0).decode("utf-8")
                    if len(txt.strip()) >= 3 and not txt.startswith("http"):
                        entries.append((0, txt.strip()))
                except Exception:
                    pass
        except Exception:
            pass

        return entries

    @staticmethod
    def build(entries: List[Tuple[int, str]]) -> bytes:
        """Encodes a list of (key_hash, string_text) into valid STBL v5 bytes."""
        total_len = sum(len(txt.encode("utf-8")) for _, txt in entries)
        buf = bytearray()
        buf.extend(b"STBL\x05\x00\x00")
        buf.extend(struct.pack("<I", len(entries)))
        buf.extend(b"\x00\x00")  # reserved
        buf.extend(struct.pack("<I", total_len))

        for key_hash, text in entries:
            encoded = text.encode("utf-8")
            buf.extend(struct.pack("<I", key_hash & 0xFFFFFFFF))
            buf.append(0)  # flags
            buf.extend(struct.pack("<H", len(encoded)))
            buf.extend(encoded)

        return bytes(buf)
