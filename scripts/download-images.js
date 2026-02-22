/**
 * Image Download Script
 * Run: node scripts/download-images.js
 *
 * Downloads placeholder images from Unsplash for development.
 * Replace with real DPS photography before going live.
 */

const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");

const OUTPUT_DIR = path.join(__dirname, "../public/images");

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const images = [
  {
    filename: "hero-bg.jpg",
    query: "heating+engineer+boiler+professional",
    description: "Home hero background",
  },
  {
    filename: "engineer-working.jpg",
    query: "plumber+engineer+pipes+working",
    description: "About / trust section",
  },
  {
    filename: "boiler-modern.jpg",
    query: "modern+boiler+white+wall",
    description: "Boiler service pages",
  },
  {
    filename: "central-heating.jpg",
    query: "central+heating+radiator+home",
    description: "Central heating pages",
  },
  {
    filename: "plumbing-pipes.jpg",
    query: "plumber+fixing+pipes+bathroom",
    description: "Plumbing pages",
  },
  {
    filename: "ac-unit-indoor.jpg",
    query: "air+conditioning+unit+interior+white",
    description: "AC pages",
  },
  {
    filename: "ac-installation.jpg",
    query: "air+conditioning+installation+technician",
    description: "AC installation page",
  },
  {
    filename: "bathroom-install.jpg",
    query: "modern+bathroom+renovation",
    description: "Bathroom plumbing page",
  },
  {
    filename: "kitchen-plumbing.jpg",
    query: "kitchen+sink+plumber",
    description: "Kitchen plumbing page",
  },
  {
    filename: "emergency-callout.jpg",
    query: "emergency+plumber+repair",
    description: "Emergency page",
  },
  {
    filename: "team-vans.jpg",
    query: "engineer+company+van+fleet",
    description: "About page / trust",
  },
  {
    filename: "service-area-map.jpg",
    query: "city+map+urban+aerial+view",
    description: "Service areas page",
  },
  {
    filename: "quote-section-bg.jpg",
    query: "modern+home+interior+dark",
    description: "Quote / contact background",
  },
];

function downloadImage(url, dest) {
  return new Promise((resolve, reject) => {
    // Skip if file already exists
    if (fs.existsSync(dest)) {
      console.log(`  ✓ Already exists: ${path.basename(dest)}`);
      return resolve();
    }

    const file = fs.createWriteStream(dest);
    const protocol = url.startsWith("https") ? https : http;

    const request = protocol.get(url, (response) => {
      // Handle redirects
      if (response.statusCode === 301 || response.statusCode === 302) {
        file.close();
        fs.unlinkSync(dest);
        return downloadImage(response.headers.location, dest).then(resolve).catch(reject);
      }

      if (response.statusCode !== 200) {
        file.close();
        fs.unlinkSync(dest);
        return reject(new Error(`HTTP ${response.statusCode} for ${url}`));
      }

      response.pipe(file);
      file.on("finish", () => {
        file.close();
        resolve();
      });
    });

    request.on("error", (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });

    file.on("error", (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function downloadAll() {
  console.log("Downloading images to /public/images/...\n");

  for (const img of images) {
    const dest = path.join(OUTPUT_DIR, img.filename);
    // Using Unsplash Source API (no API key required for development)
    const url = `https://source.unsplash.com/1600x900/?${img.query}`;

    process.stdout.write(`  Downloading ${img.filename} (${img.description})... `);
    try {
      await downloadImage(url, dest);
      console.log("done");
    } catch (err) {
      console.log(`FAILED: ${err.message}`);
      // Try a fallback URL
      try {
        const fallback = `https://picsum.photos/seed/${img.filename.replace(".jpg","")}/1600/900`;
        await downloadImage(fallback, dest);
        console.log(`  ✓ Downloaded fallback for ${img.filename}`);
      } catch (fallbackErr) {
        console.log(`  ✗ Fallback also failed for ${img.filename}: ${fallbackErr.message}`);
      }
    }
  }

  console.log("\nDone. Check /public/images/ for downloaded files.");
  console.log("Note: Replace placeholder images with real DPS photography before going live.\n");
}

downloadAll();
