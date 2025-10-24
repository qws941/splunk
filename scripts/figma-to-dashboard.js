#!/usr/bin/env node
/**
 * Figma to Splunk Dashboard Converter
 *
 * Automated workflow: Figma Design → Dashboard Studio JSON
 *
 * Features:
 * - Extract layout from Figma frames
 * - Convert colors to Dashboard Studio format
 * - Generate dataSources from annotations
 * - Create visualizations with proper positioning
 *
 * Usage:
 *   node scripts/figma-to-dashboard.js <figma-file-key> <page-name>
 *   node scripts/figma-to-dashboard.js abc123xyz "Dashboard Design"
 */

import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read Figma API key from MCP config
const FIGMA_CONFIG_PATH = path.join(process.env.HOME, '.mcp-figma', 'config.json');
let FIGMA_API_KEY;

try {
  const config = JSON.parse(fs.readFileSync(FIGMA_CONFIG_PATH, 'utf-8'));
  FIGMA_API_KEY = config.apiKey;
} catch (error) {
  console.error('❌ Error: Figma API key not found');
  console.error('   Run: node -e "require(\'child_process\').execSync(\'mcp__figma__set_api_key\')"');
  process.exit(1);
}

/**
 * Fetch Figma file data
 */
async function fetchFigmaFile(fileKey) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.figma.com',
      port: 443,
      path: `/v1/files/${fileKey}`,
      method: 'GET',
      headers: {
        'X-Figma-Token': FIGMA_API_KEY
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

/**
 * Find frames in Figma page
 */
function findFrames(node, frames = []) {
  if (node.type === 'FRAME' || node.type === 'COMPONENT') {
    frames.push(node);
  }

  if (node.children) {
    node.children.forEach(child => findFrames(child, frames));
  }

  return frames;
}

/**
 * Convert Figma color to hex
 */
function rgbaToHex(color) {
  const r = Math.round(color.r * 255);
  const g = Math.round(color.g * 255);
  const b = Math.round(color.b * 255);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * Extract visualization type from frame name
 */
function detectVisualizationType(frameName) {
  const name = frameName.toLowerCase();

  if (name.includes('table')) return 'splunk.table';
  if (name.includes('line') || name.includes('chart')) return 'splunk.line';
  if (name.includes('bar')) return 'splunk.bar';
  if (name.includes('pie')) return 'splunk.pie';
  if (name.includes('single') || name.includes('metric')) return 'splunk.singlevalue';
  if (name.includes('area')) return 'splunk.area';
  if (name.includes('column')) return 'splunk.column';

  return 'splunk.table'; // Default
}

/**
 * Extract SPL query from frame description
 */
function extractSPLQuery(description) {
  if (!description) return 'index=fw | stats count';

  // Look for SPL query in description (format: SPL: <query>)
  const spl = description.match(/SPL:\s*(.+)/i);
  if (spl) return spl[1].trim();

  // Default query
  return 'index=fw | stats count';
}

/**
 * Convert Figma frame to Dashboard Studio visualization
 */
function frameToVisualization(frame, index) {
  const vizId = `viz_${frame.name.toLowerCase().replace(/\s+/g, '_')}`;
  const dsId = `ds_${frame.name.toLowerCase().replace(/\s+/g, '_')}`;

  const vizType = detectVisualizationType(frame.name);
  const spl = extractSPLQuery(frame.description);

  const visualization = {
    type: vizType,
    options: {},
    dataSources: {
      primary: dsId
    },
    title: frame.name
  };

  // Add type-specific options
  if (vizType === 'splunk.table') {
    visualization.options = {
      count: 20,
      dataOverlayMode: 'none',
      drilldown: 'none',
      rowNumbers: true
    };
  } else if (vizType === 'splunk.singlevalue') {
    visualization.options = {
      majorValue: "> primary | seriesByName('value')",
      showSparklineAreaGraph: false
    };
  } else if (vizType === 'splunk.line') {
    visualization.options = {
      xField: '_time',
      legend: 'bottom'
    };
  }

  const dataSource = {
    type: 'ds.search',
    options: {
      query: spl,
      queryParameters: {
        earliest: '$global_time.earliest$',
        latest: '$global_time.latest$'
      },
      refresh: '1m',
      refreshType: 'delay'
    },
    name: `${frame.name} Search`
  };

  return { vizId, dsId, visualization, dataSource };
}

/**
 * Convert Figma layout to Dashboard Studio structure
 */
function framesToLayout(frames, canvasWidth = 1440) {
  // Find bounding box of all frames
  const minX = Math.min(...frames.map(f => f.absoluteBoundingBox.x));
  const minY = Math.min(...frames.map(f => f.absoluteBoundingBox.y));

  return frames.map(frame => {
    const bbox = frame.absoluteBoundingBox;

    return {
      item: `viz_${frame.name.toLowerCase().replace(/\s+/g, '_')}`,
      type: 'block',
      position: {
        x: Math.round(bbox.x - minX),
        y: Math.round(bbox.y - minY),
        w: Math.round(bbox.width),
        h: Math.round(bbox.height)
      }
    };
  });
}

/**
 * Generate Dashboard Studio JSON
 */
function generateDashboardJSON(figmaData, pageName) {
  // Find the specified page
  const page = figmaData.document.children.find(p => p.name === pageName);
  if (!page) {
    throw new Error(`Page "${pageName}" not found. Available pages: ${figmaData.document.children.map(p => p.name).join(', ')}`);
  }

  // Extract frames
  const frames = findFrames(page);
  console.log(`📊 Found ${frames.length} frames in page "${pageName}"`);

  // Convert frames to visualizations
  const visualizations = {};
  const dataSources = {};

  frames.forEach((frame, index) => {
    const { vizId, dsId, visualization, dataSource } = frameToVisualization(frame, index);
    visualizations[vizId] = visualization;
    dataSources[dsId] = dataSource;
  });

  // Generate layout
  const structure = framesToLayout(frames);

  // Calculate canvas size
  const maxX = Math.max(...structure.map(s => s.position.x + s.position.w));
  const maxY = Math.max(...structure.map(s => s.position.y + s.position.h));

  // Construct Dashboard Studio JSON
  const dashboard = {
    visualizations,
    dataSources,
    defaults: {
      dataSources: {
        'ds.search': {
          options: {
            queryParameters: {
              latest: '$global_time.latest$',
              earliest: '$global_time.earliest$'
            }
          }
        }
      }
    },
    inputs: {
      input_global_trp: {
        type: 'input.timerange',
        options: {
          token: 'global_time',
          defaultValue: '-24h@h,now'
        },
        title: '⏰ Time Range'
      }
    },
    layout: {
      type: 'grid',
      options: {
        width: Math.max(1440, maxX),
        height: maxY + 100,
        display: 'auto-scale'
      },
      structure,
      globalInputs: ['input_global_trp']
    },
    description: `Generated from Figma: ${figmaData.name}`,
    title: pageName,
    version: '1.0.0'
  };

  return dashboard;
}

/**
 * Main execution
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node scripts/figma-to-dashboard.js <figma-file-key> <page-name>');
    console.error('\nExample:');
    console.error('  node scripts/figma-to-dashboard.js abc123xyz "Dashboard Design"');
    console.error('\nTo find your Figma file key:');
    console.error('  Open Figma file → URL: https://www.figma.com/file/[FILE_KEY]/...');
    process.exit(1);
  }

  const [fileKey, pageName] = args;

  try {
    console.log('🔍 Fetching Figma file...');
    const figmaData = await fetchFigmaFile(fileKey);
    console.log(`✅ Loaded: ${figmaData.name}`);

    console.log('🔄 Converting to Dashboard Studio JSON...');
    const dashboard = generateDashboardJSON(figmaData, pageName);

    // Save to file
    const outputPath = path.join(__dirname, '..', 'configs', 'dashboards', 'studio', `${pageName.toLowerCase().replace(/\s+/g, '-')}.json`);
    fs.writeFileSync(outputPath, JSON.stringify(dashboard, null, 2));

    console.log(`✅ Dashboard created: ${outputPath}`);
    console.log('\n📊 Summary:');
    console.log(`   - Visualizations: ${Object.keys(dashboard.visualizations).length}`);
    console.log(`   - Data Sources: ${Object.keys(dashboard.dataSources).length}`);
    console.log(`   - Canvas Size: ${dashboard.layout.options.width}x${dashboard.layout.options.height}`);
    console.log('\n🚀 Next steps:');
    console.log('   1. Review generated JSON and adjust SPL queries');
    console.log('   2. Deploy to Splunk via REST API');
    console.log(`   3. curl -k -u admin:password -d "eai:data=$(cat ${outputPath})" https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/studio`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main();
