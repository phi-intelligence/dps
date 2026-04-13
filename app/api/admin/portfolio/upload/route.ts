import { NextRequest, NextResponse } from "next/server";
import { mkdir, writeFile } from "fs/promises";
import { join } from "path";
import sharp from "sharp";
import { isAdminAuthenticated } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/heic",
  "image/heif",
]);

function safeFilenamePart(input: string): string {
  return input.toLowerCase().replace(/[^a-z0-9-]/g, "-");
}

export async function POST(request: NextRequest) {
  const ok = await isAdminAuthenticated();
  if (!ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const formData = await request.formData();
    const files = formData.getAll("files").filter((f): f is File => f instanceof File);

    if (files.length === 0) {
      return NextResponse.json({ error: "No files uploaded" }, { status: 400 });
    }

    const uploadDir = join(process.cwd(), "public", "uploads", "portfolio");
    await mkdir(uploadDir, { recursive: true });

    const urls: string[] = [];

    for (const file of files) {
      if (file.size > MAX_UPLOAD_BYTES) {
        return NextResponse.json(
          { error: `File ${file.name} exceeds 10MB limit` },
          { status: 400 }
        );
      }

      if (!ALLOWED_TYPES.has(file.type)) {
        return NextResponse.json(
          { error: `Unsupported image type for ${file.name}` },
          { status: 400 }
        );
      }

      const sourceBuffer = Buffer.from(await file.arrayBuffer());
      const optimized = await sharp(sourceBuffer)
        .rotate()
        .resize({ width: 1920, height: 1920, fit: "inside", withoutEnlargement: true })
        .webp({ quality: 78 })
        .toBuffer();

      const stamp = Date.now();
      const base = safeFilenamePart(file.name.replace(/\.[^/.]+$/, "")) || "portfolio-image";
      const filename = `${base}-${stamp}-${Math.random().toString(36).slice(2, 8)}.webp`;
      const outPath = join(uploadDir, filename);

      await writeFile(outPath, optimized);
      urls.push(`/uploads/portfolio/${filename}`);
    }

    return NextResponse.json({ urls });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: "Failed to upload images" }, { status: 500 });
  }
}
