const assert = require('assert')
const fs = require('fs')
const path = require('path')

const rootDir = path.join(__dirname, '..')

function read(relativePath) {
  return fs.readFileSync(path.join(rootDir, relativePath), 'utf8')
}

function exists(relativePath) {
  return fs.existsSync(path.join(rootDir, relativePath))
}

assert.ok(exists('SKILL.md'), 'repository root must contain SKILL.md')
assert.ok(exists('agents/openai.yaml'), 'skill must include Agent UI metadata')
assert.ok(exists('scripts/enhance_brand_design_prompt.py'), 'skill must include the API caller script')
assert.ok(exists('references/api.md'), 'skill must include API usage reference')

const skill = read('SKILL.md')
assert.ok(/^---\nname: brand-design-skill\n/m.test(skill), 'SKILL.md must use the brand-design-skill name')
assert.ok(!skill.includes('TODO'), 'SKILL.md must not contain template TODO text')
assert.ok(/JAMBOX_BRAND_DESIGN_TOKEN/.test(skill), 'SKILL.md must explain the required token env var')
assert.ok(/scripts\/enhance_brand_design_prompt\.py/.test(skill), 'SKILL.md must point agents to the script')
assert.ok(/Brand Design Enhancer endpoint/.test(skill), 'SKILL.md must reference the platform enhancer endpoint')

const metadata = read('agents/openai.yaml')
assert.ok(/display_name:\s*"品牌设计增强器"/.test(metadata), 'openai.yaml must expose the Chinese display name')
assert.ok(/\$brand-design-skill/.test(metadata), 'default prompt must explicitly mention $brand-design-skill')

const script = read('scripts/enhance_brand_design_prompt.py')
assert.ok(/JAMBOX_BRAND_DESIGN_TOKEN/.test(script), 'script must read the token from the environment')
assert.ok(/JAMBOX_BRAND_DESIGN_API_BASE/.test(script), 'script must allow overriding the API base')
assert.ok(/\/api\/brand-design-enhancer\/enhance/.test(script), 'script must call the JamBox enhancer endpoint')
assert.ok(/\/brand-design-enhancer\/enhance/.test(script), 'script must support the API domain enhancer endpoint')
assert.ok(!/api_key|OPENAI_API_KEY|sk-/.test(script), 'script must not ask for or embed upstream model keys')

const apiReference = read('references/api.md')
assert.ok(/https:\/\/api\.jamboxclaw\.com/.test(apiReference), 'API reference must document the production API base')
assert.ok(/https:\/\/api\.jamboxclaw\.com\/brand-design-enhancer\/enhance/.test(apiReference), 'API reference must document the production endpoint')
assert.ok(/Authorization: Bearer/.test(apiReference), 'API reference must document bearer authentication')
assert.ok(/chargedCredits/.test(apiReference), 'API reference must document returned credit usage')

console.log('brand-design-skill validation passed')
