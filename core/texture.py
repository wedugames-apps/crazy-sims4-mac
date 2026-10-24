"""
==============================================================================
Crazy The Sims 4 Project - Texture Processor & VRAM Optimizer
==============================================================================
Analyzes texture dimensions in Sims 4 packages (PNG, DDS, DST, RLE2) and downsamples
unoptimized 4K/8K CC textures to high-performance 2K Lanczos.
"""

import io
import struct
from typing import Dict, List, Optional, Tuple
from PIL import Image

from core.dbpf import TYPE_DST, TYPE_PNG, TYPE_RLE2, TYPE_RLES, DBPFPackage, DBPFResource


class TextureInfo:
    """Represents analyzed texture metadata."""

    def __init__(
        self,
        tgi: str,
        res_type: int,
        width: int,
        height: int,
        format_name: str,
        size_bytes: int,
        is_oversized: bool = False
    ):
        self.tgi: str = tgi
        self.res_type: int = res_type
        self.width: int = width
        self.height: int = height
        self.format_name: str = format_name
        self.size_bytes: int = size_bytes
        self.is_oversized: bool = is_oversized or (width > 2048 or height > 2048)

    @property
    def dimensions_str(self) -> str:
        return f"{self.width}x{self.height}"

    def __repr__(self) -> str:
        return f"<TextureInfo {self.dimensions_str} {self.format_name} Oversized={self.is_oversized}>"


class TextureProcessor:
    """Inspects and optimizes textures for The Sims 4."""

    MAX_SAFE_DIMENSION = 2048  # Standard Sims 4 max texture dimension (2K)

    @staticmethod
    def inspect_texture_bytes(data: bytes, res_type: int, tgi: str = "") -> Optional[TextureInfo]:
        """
        Parses texture header to extract width and height without full decompression if possible.
        Supports PNG, DDS, DST, and RLE2.
        """
        if not data or len(data) < 16:
            return None

        # 1. Standard PNG
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            try:
                w, h = struct.unpack_from(">II", data, 16)
                return TextureInfo(tgi, res_type, w, h, "PNG", len(data))
            except Exception:
                pass

        # 2. DDS / DirectDraw Surface
        if data[:4] == b"DDS ":
            try:
                h, w = struct.unpack_from("<II", data, 12)
                return TextureInfo(tgi, res_type, w, h, "DDS", len(data))
            except Exception:
                pass

        # 3. RLE2 / Sims 4 Texture
        if data[:4] == b"RLE2":
            try:
                version = struct.unpack_from("<I", data, 4)[0]
                w, h = struct.unpack_from("<HH", data, 8)
                return TextureInfo(tgi, res_type, w, h, "RLE2", len(data))
            except Exception:
                pass

        # 4. Fallback via Pillow
        try:
            with Image.open(io.BytesIO(data)) as img:
                w, h = img.size
                fmt = img.format or "UNKNOWN"
                return TextureInfo(tgi, res_type, w, h, fmt, len(data))
        except Exception:
            return None

    @classmethod
    def downsample_image(
        cls,
        image_bytes: bytes,
        max_dim: int = MAX_SAFE_DIMENSION
    ) -> Tuple[bytes, bool, int, int]:
        """
        Downsamples an image if either width or height exceeds max_dim.
        Uses Pillow's high-quality Lanczos resampling.
        Returns: (result_bytes, was_downsampled, new_w, new_h)
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                w, h = img.size
                if w <= max_dim and h <= max_dim:
                    return image_bytes, False, w, h

                # Calculate new aspect ratio
                if w >= h:
                    new_w = max_dim
                    new_h = max(1, int(h * (max_dim / w)))
                else:
                    new_h = max_dim
                    new_w = max(1, int(w * (max_dim / h)))

                # Perform high-quality Lanczos downsampling
                resized = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

                out_buf = io.BytesIO()
                fmt = img.format if img.format in ("PNG", "JPEG", "WEBP", "DDS") else "PNG"
                if fmt == "DDS":
                    try:
                        resized.save(out_buf, format="DDS")
                    except Exception:
                        resized.save(out_buf, format="PNG")
                elif fmt == "PNG":
                    resized.save(out_buf, format="PNG", optimize=True)
                else:
                    resized.save(out_buf, format=fmt)

                return out_buf.getvalue(), True, new_w, new_h
        except Exception:
            return image_bytes, False, 0, 0

    @classmethod
    def analyze_package_textures(cls, pkg: DBPFPackage) -> Dict[str, any]:
        """
        Finds all texture resources in a package and checks for 4K/8K oversized files.
        """
        texture_types = {TYPE_PNG, TYPE_DST, TYPE_RLE2, TYPE_RLES}
        textures: List[TextureInfo] = []
        oversized_count = 0
        total_texture_size = 0

        for r in pkg.resources:
            if r.res_type in texture_types:
                t_info = cls.inspect_texture_bytes(r.data, r.res_type, tgi=r.tgi)
                if t_info:
                    textures.append(t_info)
                    total_texture_size += t_info.size_bytes
                    if t_info.is_oversized:
                        oversized_count += 1

        return {
            "total_textures": len(textures),
            "oversized_count": oversized_count,
            "total_texture_size": total_texture_size,
            "textures": textures
        }

    @classmethod
    def optimize_package_textures(
        cls,
        pkg: DBPFPackage,
        max_dim: int = MAX_SAFE_DIMENSION
    ) -> Tuple[int, int]:
        """
        Downsamples all oversized textures (PNG, DST/DDS) in a package.
        Returns: (downsampled_count, bytes_saved)
        """
        downsampled = 0
        bytes_saved = 0
        target_types = {TYPE_PNG, TYPE_DST}

        for r in pkg.resources:
            if r.res_type in target_types:
                old_size = len(r.data)
                new_data, changed, _, _ = cls.downsample_image(r.data, max_dim=max_dim)
                if changed:
                    r.data = new_data
                    if len(new_data) < old_size:
                        bytes_saved += (old_size - len(new_data))
                    downsampled += 1

        return downsampled, bytes_saved


TextureDownsampler = TextureProcessor
