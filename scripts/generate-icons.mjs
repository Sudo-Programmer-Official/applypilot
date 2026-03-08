import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const currentFilePath = fileURLToPath(import.meta.url)
const currentDir = path.dirname(currentFilePath)
const projectRoot = path.resolve(currentDir, '..')

const input = path.join(projectRoot, 'assets/logo.png')
const outputDir = path.join(projectRoot, 'apps/web/public/icons')
const ogImageOutput = path.join(projectRoot, 'apps/web/public/og-image.png')

const sizes = [16, 32, 48, 72, 96, 128, 144, 152, 180, 192, 384, 512]
const transparentBackground = { r: 255, g: 255, b: 255, alpha: 0 }

function ensureDirectory(directoryPath) {
  if (!fs.existsSync(directoryPath)) {
    fs.mkdirSync(directoryPath, { recursive: true })
  }
}

async function loadTrimmedLogoBuffer() {
  if (!fs.existsSync(input)) {
    throw new Error(`Missing master logo at ${input}`)
  }

  return sharp(input).trim().png().toBuffer()
}

async function generateOpenGraphImage(trimmedLogoBuffer) {
  const width = 1200
  const height = 630
  const background = Buffer.from(`
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#FBFAF6" />
          <stop offset="100%" stop-color="#E7EEF8" />
        </linearGradient>
        <radialGradient id="glowA" cx="18%" cy="22%" r="40%">
          <stop offset="0%" stop-color="#F59E0B" stop-opacity="0.24" />
          <stop offset="100%" stop-color="#F59E0B" stop-opacity="0" />
        </radialGradient>
        <radialGradient id="glowB" cx="88%" cy="18%" r="42%">
          <stop offset="0%" stop-color="#2563EB" stop-opacity="0.18" />
          <stop offset="100%" stop-color="#2563EB" stop-opacity="0" />
        </radialGradient>
      </defs>
      <rect width="${width}" height="${height}" rx="36" fill="url(#bg)" />
      <rect x="44" y="44" width="${width - 88}" height="${height - 88}" rx="32" fill="rgba(255,255,255,0.88)" />
      <circle cx="214" cy="178" r="240" fill="url(#glowA)" />
      <circle cx="1030" cy="132" r="260" fill="url(#glowB)" />
      <text x="618" y="220" fill="#8B5E34" font-size="24" font-family="Arial, Helvetica, sans-serif" font-weight="700" letter-spacing="6">APPLYPILOT</text>
      <text x="618" y="302" fill="#14213D" font-size="62" font-family="Georgia, serif" font-weight="700">Optimize every</text>
      <text x="618" y="376" fill="#14213D" font-size="62" font-family="Georgia, serif" font-weight="700">resume with</text>
      <text x="618" y="450" fill="#14213D" font-size="62" font-family="Georgia, serif" font-weight="700">guided flow.</text>
      <text x="618" y="520" fill="#5F6C80" font-size="28" font-family="Arial, Helvetica, sans-serif">
        Upload, review, optimize, and export ATS-safe resumes.
      </text>
    </svg>
  `)

  const logoBuffer = await sharp(trimmedLogoBuffer)
    .resize({
      width: 420,
      height: 420,
      fit: 'contain',
      background: transparentBackground,
    })
    .png()
    .toBuffer()

  await sharp(background)
    .composite([
      {
        input: logoBuffer,
        left: 120,
        top: 105,
      },
    ])
    .png()
    .toFile(ogImageOutput)

  console.log(`Generated ${path.relative(projectRoot, ogImageOutput)}`)
}

async function generate() {
  ensureDirectory(outputDir)

  const trimmedLogoBuffer = await loadTrimmedLogoBuffer()

  for (const size of sizes) {
    const output =
      size === 180
        ? path.join(outputDir, 'apple-touch-icon.png')
        : path.join(outputDir, `icon-${size}x${size}.png`)

    await sharp(trimmedLogoBuffer)
      .resize({
        width: size,
        height: size,
        fit: 'contain',
        background: transparentBackground,
      })
      .png()
      .toFile(output)

    console.log(`Generated ${path.relative(projectRoot, output)}`)
  }

  const faviconOutput = path.join(outputDir, 'favicon.png')
  await sharp(trimmedLogoBuffer)
    .resize({
      width: 32,
      height: 32,
      fit: 'contain',
      background: transparentBackground,
    })
    .png()
    .toFile(faviconOutput)

  console.log(`Generated ${path.relative(projectRoot, faviconOutput)}`)

  await generateOpenGraphImage(trimmedLogoBuffer)

  console.log('Icon generation complete')
}

generate().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
