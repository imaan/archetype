/**
 * Standalone validation: ab-downloader for Instagram extraction.
 * Run: npx --yes ab-downloader && node input-engine/tests/standalone/test_instagram_abdownloader.mjs
 *
 * This tests the same library used in the working invisible-inbox project.
 * ab-downloader bypasses Instagram's GraphQL API (which returns 403 for instaloader).
 */

import { igdl } from 'ab-downloader';

const TEST_POSTS = [
  {
    url: 'https://www.instagram.com/reel/DFuFMKWS0bz/',
    category: 'Public reel',
    description: 'Public reel — video extraction test',
  },
  {
    url: 'https://www.instagram.com/p/C4lHxGWOb1e/',
    category: 'Public photo post',
    description: 'NASA post — large public account',
  },
  {
    url: 'https://www.instagram.com/reel/C4X7OFcOLgE/',
    category: 'Public reel (alt)',
    description: 'Another public reel',
  },
  {
    url: 'https://www.instagram.com/p/INVALID_FAKE_POST/',
    category: 'Invalid post',
    description: 'Non-existent post — should fail gracefully',
  },
];

async function testPost(postInfo) {
  const result = {
    url: postInfo.url,
    category: postInfo.category,
    success: false,
    mediaCount: 0,
    mediaUrls: [],
    thumbnails: [],
    error: null,
    timeMs: 0,
  };

  const start = Date.now();
  try {
    const data = await igdl(postInfo.url);
    result.timeMs = Date.now() - start;

    if (data && Array.isArray(data) && data.length > 0) {
      result.success = true;
      result.mediaCount = data.length;
      result.mediaUrls = data.map(d => d.url).filter(Boolean);
      result.thumbnails = data.map(d => d.thumbnail).filter(Boolean);
    } else {
      result.error = 'No data returned (empty array or null)';
    }
  } catch (e) {
    result.timeMs = Date.now() - start;
    result.error = `${e.constructor.name}: ${e.message}`;
  }

  return result;
}

function printResult(result, index) {
  const status = result.success ? 'PASS' : 'FAIL';
  console.log(`\n${'='.repeat(70)}`);
  console.log(`Test ${index + 1}: [${status}] ${result.category}`);
  console.log(`URL: ${result.url}`);
  console.log(`Time: ${result.timeMs}ms`);

  if (result.error) {
    console.log(`Error: ${result.error}`);
  } else {
    console.log(`Media count: ${result.mediaCount}`);
    result.mediaUrls.forEach((url, i) => {
      console.log(`  Media ${i + 1}: ${url.substring(0, 100)}...`);
    });
    if (result.thumbnails.length) {
      console.log(`Thumbnails: ${result.thumbnails.length}`);
    }
  }
}

async function main() {
  console.log('='.repeat(70));
  console.log('INSTAGRAM EXTRACTION — ab-downloader VALIDATION');
  console.log('(Same library used in working invisible-inbox project)');
  console.log('='.repeat(70));

  const results = [];

  for (let i = 0; i < TEST_POSTS.length; i++) {
    const post = TEST_POSTS[i];
    console.log(`\n>>> Testing ${i + 1}/${TEST_POSTS.length}: ${post.description}`);

    const result = await testPost(post);
    results.push(result);
    printResult(result, i);

    // Delay between requests
    if (i < TEST_POSTS.length - 1) {
      console.log('\n  Waiting 3s...');
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  // Summary
  console.log(`\n${'='.repeat(70)}`);
  console.log('SUMMARY');
  console.log('='.repeat(70));

  const passed = results.filter(r => r.success).length;
  console.log(`Passed: ${passed}/${results.length}`);
  console.log();

  for (const r of results) {
    const status = r.success ? 'PASS' : 'FAIL';
    const media = r.success ? `${r.mediaCount} media` : r.error?.substring(0, 50);
    console.log(`  ${status.padEnd(6)} ${r.category.padEnd(25)} ${r.timeMs}ms  ${media}`);
  }

  console.log('\n\n--- JSON OUTPUT ---');
  console.log(JSON.stringify(results, null, 2));
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
