#!/usr/bin/env python3
"""
Image Compressor GUI
=====================
A simple desktop tool to pick an image from a folder and compress it,
built with Tkinter + Pillow.

Features
--------
- Browse and pick an image file (jpg, png, webp, bmp, tiff, etc.)
- Live preview of the original image + file size
- Compression controls:
    * JPEG/WebP quality slider (1-95)
    * Optional resize (max width/height, keeps aspect ratio)
    * Optional convert to a different format on save (JPEG / PNG / WEBP)
    * PNG optimize + palette reduction option
- Shows resulting file size and % reduction after saving
- "Save As" so you choose where the compressed image goes

Requirements
------------
    pip install Pillow

Run
---
    python image_compressor_gui.py
"""

import os
import io
import threading
from tkinter import (
    Tk, Frame, Label, Button, Scale, StringVar, IntVar, DoubleVar,
    filedialog, messagebox, HORIZONTAL, LEFT, RIGHT, TOP, BOTTOM,
    X, Y, BOTH, W, E, N, S, ttk
)

from PIL import Image, ImageTk, ImageOps

SUPPORTED_EXTS = [
    ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif"),
    ("All files", "*.*"),
]

FORMAT_CHOICES = ["Keep original", "JPEG", "PNG", "WEBP"]


def human_size(num_bytes: int) -> str:
    """Format a byte count as a human-readable string."""
    step = 1024.0
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < step:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= step
    return f"{num_bytes:.1f} TB"


class ImageCompressorApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Image Compressor")
        self.root.geometry("880x620")
        self.root.minsize(760, 560)

        self.src_path = None
        self.src_image = None          # PIL Image, original, unmodified
        self.preview_photo = None      # ImageTk.PhotoImage kept alive
        self.original_size_bytes = 0

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = self.root

        # --- Top bar: file selection -----------------------------------
        top = Frame(root, padx=10, pady=10)
        top.pack(side=TOP, fill=X)

        Button(top, text="Select Image…", command=self.select_image).pack(side=LEFT)

        self.path_var = StringVar(value="No image selected")
        Label(top, textvariable=self.path_var, anchor=W, fg="#444").pack(
            side=LEFT, padx=10, fill=X, expand=True
        )

        # --- Middle: preview + controls side by side --------------------
        middle = Frame(root, padx=10)
        middle.pack(side=TOP, fill=BOTH, expand=True)

        # Preview panel
        preview_frame = Frame(middle, bd=1, relief="solid", bg="#f7f7f7")
        preview_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10), pady=5)

        self.preview_label = Label(preview_frame, bg="#f7f7f7", text="Preview will appear here")
        self.preview_label.pack(fill=BOTH, expand=True)

        self.info_var = StringVar(value="")
        Label(preview_frame, textvariable=self.info_var, bg="#f7f7f7", fg="#555").pack(
            side=BOTTOM, pady=6
        )

        # Controls panel
        controls = Frame(middle, width=300)
        controls.pack(side=RIGHT, fill=Y, pady=5)
        controls.pack_propagate(False)

        Label(controls, text="Compression Settings", font=("Segoe UI", 11, "bold")).pack(
            anchor=W, pady=(0, 8)
        )

        # Output format
        Label(controls, text="Output format:").pack(anchor=W)
        self.format_var = StringVar(value=FORMAT_CHOICES[0])
        fmt_menu = ttk.Combobox(
            controls, textvariable=self.format_var, values=FORMAT_CHOICES,
            state="readonly"
        )
        fmt_menu.pack(fill=X, pady=(0, 10))
        fmt_menu.bind("<<ComboboxSelected>>", lambda e: self._sync_quality_state())

        # Quality slider (JPEG/WEBP)
        Label(controls, text="Quality (JPEG / WEBP):").pack(anchor=W)
        self.quality_var = IntVar(value=75)
        self.quality_scale = Scale(
            controls, from_=1, to=95, orient=HORIZONTAL, variable=self.quality_var
        )
        self.quality_scale.pack(fill=X, pady=(0, 10))

        # Resize option
        self.resize_enabled = IntVar(value=0)
        ttk.Checkbutton(
            controls, text="Resize (max dimension, keep aspect ratio)",
            variable=self.resize_enabled, command=self._sync_resize_state
        ).pack(anchor=W)

        resize_row = Frame(controls)
        resize_row.pack(fill=X, pady=(0, 10))
        Label(resize_row, text="Max width/height (px):").pack(side=LEFT)
        self.max_dim_var = IntVar(value=1920)
        self.max_dim_entry = ttk.Entry(resize_row, textvariable=self.max_dim_var, width=8)
        self.max_dim_entry.pack(side=LEFT, padx=6)

        # PNG optimize / palette
        self.png_optimize_var = IntVar(value=1)
        ttk.Checkbutton(
            controls, text="PNG: optimize + reduce colors (palette)",
            variable=self.png_optimize_var
        ).pack(anchor=W, pady=(0, 4))

        # Strip metadata
        self.strip_meta_var = IntVar(value=1)
        ttk.Checkbutton(
            controls, text="Strip metadata (EXIF etc.)",
            variable=self.strip_meta_var
        ).pack(anchor=W, pady=(0, 14))

        # Buttons
        self.compress_btn = Button(
            controls, text="Compress && Preview", command=self.compress_preview,
            state="disabled"
        )
        self.compress_btn.pack(fill=X, pady=(0, 6))

        self.save_btn = Button(
            controls, text="Save Compressed As…", command=self.save_compressed,
            state="disabled"
        )
        self.save_btn.pack(fill=X)

        # Result info
        self.result_var = StringVar(value="")
        Label(controls, textvariable=self.result_var, fg="#0a6b0a", justify=LEFT,
              wraplength=280).pack(anchor=W, pady=(14, 0))

        # Status bar
        self.status_var = StringVar(value="Ready.")
        status = Label(root, textvariable=self.status_var, bd=1, relief="sunken", anchor=W)
        status.pack(side=BOTTOM, fill=X)

        self._sync_quality_state()
        self._sync_resize_state()

        # cache of last compressed bytes/format for saving
        self._compressed_bytes = None
        self._compressed_format = None
        self._compressed_image_for_preview = None

    def _sync_quality_state(self):
        fmt = self.format_var.get()
        if fmt == "PNG":
            self.quality_scale.configure(state="disabled")
        else:
            self.quality_scale.configure(state="normal")

    def _sync_resize_state(self):
        state = "normal" if self.resize_enabled.get() else "disabled"
        self.max_dim_entry.configure(state=state)

    # ------------------------------------------------------------- actions
    def select_image(self):
        path = filedialog.askopenfilename(title="Select an image", filetypes=SUPPORTED_EXTS)
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open image:\n{exc}")
            return

        self.src_path = path
        self.src_image = img
        self.original_size_bytes = os.path.getsize(path)
        self.path_var.set(path)
        self.result_var.set("")
        self._compressed_bytes = None
        self.save_btn.configure(state="disabled")
        self.compress_btn.configure(state="normal")

        self._show_preview(img)
        self.info_var.set(
            f"{img.format or '?'} | {img.width}x{img.height} px | "
            f"{human_size(self.original_size_bytes)}"
        )
        self.status_var.set(f"Loaded: {os.path.basename(path)}")

    def _show_preview(self, pil_image):
        # Fit into a bounded box for display, without mutating original
        display = pil_image.copy()
        display = ImageOps.exif_transpose(display)
        display.thumbnail((520, 460))
        if display.mode not in ("RGB", "RGBA"):
            display = display.convert("RGBA")
        self.preview_photo = ImageTk.PhotoImage(display)
        self.preview_label.configure(image=self.preview_photo, text="")

    def _build_output_image(self):
        """Apply resize + return a working copy of the source image."""
        img = ImageOps.exif_transpose(self.src_image.copy())

        if self.resize_enabled.get():
            try:
                max_dim = int(self.max_dim_var.get())
            except Exception:
                max_dim = max(img.width, img.height)
            if max_dim > 0:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)

        return img

    def _target_format_and_ext(self):
        fmt_choice = self.format_var.get()
        if fmt_choice == "Keep original":
            ext = os.path.splitext(self.src_path)[1].lower().lstrip(".")
            fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
            fmt = fmt_map.get(ext, (self.src_image.format or "JPEG"))
        else:
            fmt = fmt_choice
        ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(fmt, ".jpg")
        return fmt, ext

    def _save_kwargs(self, fmt):
        kwargs = {}
        if fmt == "JPEG":
            kwargs["quality"] = int(self.quality_var.get())
            kwargs["optimize"] = True
            kwargs["progressive"] = True
        elif fmt == "WEBP":
            kwargs["quality"] = int(self.quality_var.get())
            kwargs["method"] = 6
        elif fmt == "PNG":
            kwargs["optimize"] = bool(self.png_optimize_var.get())
        return kwargs

    def compress_preview(self):
        if self.src_image is None:
            return
        self.status_var.set("Compressing…")
        self.root.update_idletasks()

        def work():
            try:
                img = self._build_output_image()
                fmt, _ext = self._target_format_and_ext()

                if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                if fmt == "PNG" and self.png_optimize_var.get():
                    # Reduce to an adaptive palette to shrink size, if not already low-color.
                    # Use quantize() rather than convert("P", ...): convert() drops the alpha
                    # channel entirely (transparent pixels turn solid black), while quantize()
                    # preserves transparency in the resulting palette image.
                    if img.mode != "P":
                        method = Image.FASTOCTREE if img.mode in ("RGBA", "LA") else Image.MEDIANCUT
                        img = img.quantize(colors=256, method=method)

                if self.strip_meta_var.get():
                    # Drop metadata (exif, icc profile, dpi, etc.) by clearing img.info,
                    # but keep "transparency" -- without it a P-mode PNG's palette index
                    # for transparent pixels renders as opaque instead. Note: rebuilding
                    # pixel data via Image.new()+paste() (an earlier approach) silently
                    # discards an RGBA-valued palette (as produced by quantizing an RGBA
                    # source), turning transparent areas solid black -- so metadata is
                    # stripped in place instead of reconstructing the image.
                    img.info = {k: v for k, v in img.info.items() if k == "transparency"}

                buf = io.BytesIO()
                img.save(buf, format=fmt, **self._save_kwargs(fmt))
                data = buf.getvalue()

                self._compressed_bytes = data
                self._compressed_format = fmt
                self._compressed_image_for_preview = img

                self.root.after(0, lambda: self._on_compress_done(img, data))
            except Exception as exc:
                self.root.after(0, lambda: self._on_compress_error(exc))

        threading.Thread(target=work, daemon=True).start()

    def _on_compress_done(self, img, data):
        self._show_preview(img)
        new_size = len(data)
        reduction = 0.0
        if self.original_size_bytes:
            reduction = 100.0 * (1 - new_size / self.original_size_bytes)
        self.result_var.set(
            f"Compressed size: {human_size(new_size)}\n"
            f"Original size: {human_size(self.original_size_bytes)}\n"
            f"Reduction: {reduction:.1f}%"
        )
        self.save_btn.configure(state="normal")
        self.status_var.set("Compression preview ready. Click 'Save Compressed As…' to write the file.")

    def _on_compress_error(self, exc):
        messagebox.showerror("Compression failed", str(exc))
        self.status_var.set("Compression failed.")

    def save_compressed(self):
        if not self._compressed_bytes:
            return
        _fmt, ext = self._target_format_and_ext()
        default_name = os.path.splitext(os.path.basename(self.src_path))[0] + "_compressed" + ext
        out_path = filedialog.asksaveasfilename(
            title="Save compressed image as",
            initialfile=default_name,
            defaultextension=ext,
            filetypes=[(f"{self._compressed_format} file", f"*{ext}"), ("All files", "*.*")],
        )
        if not out_path:
            return
        try:
            with open(out_path, "wb") as f:
                f.write(self._compressed_bytes)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self.status_var.set(f"Saved: {out_path}")
        messagebox.showinfo("Saved", f"Compressed image saved to:\n{out_path}")


def main():
    root = Tk()
    try:
        # Nicer default theme where available
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = ImageCompressorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
