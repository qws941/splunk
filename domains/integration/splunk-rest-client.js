/**
 * Splunk REST API Client
 * Purpose: Query Splunk via REST API without server-side modifications
 * No restart required - external service approach
 */

import https from 'https';
import { URLSearchParams } from 'url';

export default class SplunkRestClient {
  constructor(config) {
    this.host = config.host || process.env.SPLUNK_HOST;
    this.port = config.port || process.env.SPLUNK_PORT || 8089;
    this.username = config.username || process.env.SPLUNK_USERNAME || 'admin';
    this.password = config.password || process.env.SPLUNK_PASSWORD;
    this.scheme = config.scheme || 'https';

    if (!this.host || !this.password) {
      throw new Error('SPLUNK_HOST and SPLUNK_PASSWORD are required');
    }
  }

  /**
   * Execute Splunk search and get results
   * @param {string} query - SPL query
   * @param {object} options - Search options (earliest_time, latest_time, max_count)
   * @returns {Promise<Array>} - Search results
   */
  async executeSearch(query, options = {}) {
    const {
      earliest_time = '-5m',
      latest_time = 'now',
      max_count = 100,
      output_mode = 'json'
    } = options;

    try {
      // Step 1: Create search job
      const searchParams = new URLSearchParams({
        search: query,
        earliest_time,
        latest_time,
        output_mode
      });

      const jobResponse = await this.request('POST', '/services/search/jobs', searchParams.toString());
      const sid = jobResponse.sid;

      if (!sid) {
        throw new Error('Failed to create search job');
      }

      // Step 2: Wait for job completion
      await this.waitForJob(sid);

      // Step 3: Get results
      const results = await this.getJobResults(sid, max_count);

      // Step 4: Delete job
      await this.deleteJob(sid);

      return results;
    } catch (error) {
      console.error('❌ Splunk search error:', error.message);
      throw error;
    }
  }

  /**
   * Wait for search job to complete
   * @param {string} sid - Search job ID
   * @returns {Promise<void>}
   */
  async waitForJob(sid, maxWait = 30000) {
    const startTime = Date.now();
    const pollInterval = 500; // 500ms

    while (Date.now() - startTime < maxWait) {
      const status = await this.request('GET', `/services/search/jobs/${sid}`);

      if (status.entry && status.entry[0]) {
        const content = status.entry[0].content;
        const isDone = content.isDone;
        const isFailed = content.isFailed;

        if (isDone) {
          return;
        }

        if (isFailed) {
          throw new Error('Search job failed');
        }
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error('Search job timeout');
  }

  /**
   * Get search job results
   * @param {string} sid - Search job ID
   * @param {number} maxCount - Maximum results
   * @returns {Promise<Array>}
   */
  async getJobResults(sid, maxCount = 100) {
    const params = new URLSearchParams({
      output_mode: 'json',
      count: maxCount
    });

    const response = await this.request('GET', `/services/search/jobs/${sid}/results?${params}`);

    if (response.results) {
      return response.results;
    }

    return [];
  }

  /**
   * Delete search job
   * @param {string} sid - Search job ID
   * @returns {Promise<void>}
   */
  async deleteJob(sid) {
    try {
      await this.request('DELETE', `/services/search/jobs/${sid}`);
    } catch (error) {
      // Ignore delete errors
      console.warn('⚠️ Failed to delete job:', sid);
    }
  }

  /**
   * Make HTTP request to Splunk REST API
   * @param {string} method - HTTP method
   * @param {string} path - API path
   * @param {string} body - Request body
   * @returns {Promise<object>}
   */
  request(method, path, body = null) {
    return new Promise((resolve, reject) => {
      const auth = Buffer.from(`${this.username}:${this.password}`).toString('base64');

      const options = {
        hostname: this.host,
        port: this.port,
        path: path,
        method: method,
        headers: {
          'Authorization': `Basic ${auth}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        rejectUnauthorized: false // Accept self-signed certificates
      };

      if (body && method !== 'GET') {
        options.headers['Content-Length'] = Buffer.byteLength(body);
      }

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const parsed = JSON.parse(data);
              resolve(parsed);
            } catch (e) {
              resolve({ raw: data });
            }
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      if (body && method !== 'GET') {
        req.write(body);
      }

      req.end();
    });
  }

  /**
   * Test connection to Splunk
   * @returns {Promise<boolean>}
   */
  async testConnection() {
    try {
      const response = await this.request('GET', '/services/server/info');
      console.log('✅ Splunk connection successful');
      console.log(`   Version: ${response.entry?.[0]?.content?.version || 'Unknown'}`);
      return true;
    } catch (error) {
      console.error('❌ Splunk connection failed:', error.message);
      return false;
    }
  }
}
