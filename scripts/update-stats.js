const fs = require('fs');

const EXTENSIONS = [
  { name: 'Tab Suspender Pro', id: 'ofgncemnlblfnocjbojdhamacfffcpnm' },
  { name: 'BeLikeNative', id: 'fphfgdknbpakeedbaenojjdcdoajihik' },
];

async function getExtensionStats(extensionId) {
  // Use the CWS internal API that returns structured data
  // This endpoint is used by the CWS frontend and returns JSON-ish data
  const urls = [
    `https://chrome.google.com/webstore/ajax/detail?hl=en&gl=US&pv=20210820&mce=atf%2Cpii%2Crtr%2Crlb%2Cgtc%2Chcn%2Csvp%2Cwtd%2Chap%2Cnma%2Cdpb%2Car%2Cme%2Cctm%2Cac&id=${extensionId}`,
    `https://chromewebstore.google.com/detail/${extensionId}`,
  ];

  for (const url of urls) {
    try {
      const res = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
          'Accept': '*/*',
          'Accept-Language': 'en-US,en;q=0.9',
        },
      });
      const text = await res.text();

      // Try multiple patterns for user count extraction
      const patterns = [
        // JSON-style: "100,000+ users" or "1,000 users"
        /(\d[\d,]+)\+?\s*users/gi,
        // Structured data patterns
        /"userCount"[:\s]*"?(\d[\d,]*)/gi,
        // Number followed by "users" in various contexts
        /[\s>"](\d{1,3}(?:,\d{3})*(?:\+)?)\s*users/gi,
      ];

      for (const pattern of patterns) {
        const matches = [...text.matchAll(pattern)];
        for (const match of matches) {
          const numStr = match[1].replace(/[,+]/g, '');
          const count = parseInt(numStr, 10);
          if (count >= 10) { // filter out noise
            console.log(`  ${extensionId}: ${count} users (from ${url.includes('ajax') ? 'ajax API' : 'detail page'})`);
            return count;
          }
        }
      }
    } catch (err) {
      console.log(`  ${extensionId}: fetch error for ${url}: ${err.message}`);
    }
  }

  console.log(`  ${extensionId}: could not extract user count`);
  return null;
}

async function main() {
  console.log('Fetching CWS stats...');
  let totalUsers = 0;
  let foundAny = false;

  for (const ext of EXTENSIONS) {
    const users = await getExtensionStats(ext.id);
    if (users !== null) {
      totalUsers += users;
      foundAny = true;
    }
  }

  // Don't update if we couldn't fetch any stats — preserve existing values
  if (!foundAny) {
    console.log('Could not fetch any extension stats, preserving existing values');
    return;
  }

  const readme = fs.readFileSync('README.md', 'utf8');
  const statsLine = `**Zovo extensions:** 20 live · ${totalUsers.toLocaleString()}+ total users · Updated ${new Date().toISOString().split('T')[0]}`;

  const updated = readme.replace(
    /<!-- STATS:START -->[\s\S]*?<!-- STATS:END -->/,
    `<!-- STATS:START -->\n${statsLine}\n<!-- STATS:END -->`
  );

  if (updated !== readme) {
    fs.writeFileSync('README.md', updated);
    console.log('Updated stats:', statsLine);
  } else {
    console.log('No STATS markers found in README, skipping');
  }
}

main().catch(console.error);
