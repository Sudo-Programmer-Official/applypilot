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
const smallIconSizes = new Set([16, 32, 48])

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

function createSmallIconSvg() {
  return `
    <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="tile" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#162347" />
          <stop offset="100%" stop-color="#2563EB" />
        </linearGradient>
        <linearGradient id="glow" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.24" />
          <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
        </linearGradient>
      </defs>
      <rect width="48" height="48" rx="14" fill="url(#tile)" />
      <rect x="1.5" y="1.5" width="45" height="45" rx="12.5" fill="url(#glow)" />
      <path d="M15 10H28.5L35 16.5V34C35 35.657 33.657 37 32 37H15C13.343 37 12 35.657 12 34V13C12 11.343 13.343 10 15 10Z" fill="#F8FBFF" />
      <path d="M28.5 10V16.5H35" fill="#D5E6FF" />
      <path d="M14 33C16.4 30.4 18.2 27.8 20.3 24.4" stroke="#F59E0B" stroke-width="3" stroke-linecap="round" />
      <path d="M11.5 36.5C13.4 34.6 14.9 32.8 16.8 30.5" stroke="#FB923C" stroke-width="2.4" stroke-linecap="round" />
      <path d="M18 25L22.2 29.2L30.5 20.8" fill="none" stroke="#22C55E" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
  `
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
  const smallIconBuffer = Buffer.from(createSmallIconSvg())

  for (const size of sizes) {
    const output =
      size === 180
        ? path.join(outputDir, 'apple-touch-icon.png')
        : path.join(outputDir, `icon-${size}x${size}.png`)

    const sourceBuffer = smallIconSizes.has(size) ? smallIconBuffer : trimmedLogoBuffer
    const fitMode = smallIconSizes.has(size) ? 'cover' : 'contain'

    await sharp(sourceBuffer)
      .resize({
        width: size,
        height: size,
        fit: fitMode,
        background: transparentBackground,
      })
      .png()
      .toFile(output)

    console.log(`Generated ${path.relative(projectRoot, output)}`)
  }

  const faviconOutput = path.join(outputDir, 'favicon.png')
  await sharp(smallIconBuffer)
    .resize({
      width: 32,
      height: 32,
      fit: 'cover',
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
