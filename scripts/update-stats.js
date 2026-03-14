const fs = require('fs');

const EXTENSIONS = [
  { name: 'Tab Suspender Pro', id: 'ofgncemnlblfnocjbojdhamacfffcpnm' },
  { name: 'BeLikeNative', id: 'fphfgdknbpakeedbaenojjdcdoajihik' },
];

async function getExtensionStats(extensionId) {
  try {
    const res = await fetch(
      `https://chromewebstore.google.com/detail/${extensionId}`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml',
          'Accept-Language': 'en-US,en;q=0.9',
        },
      }
    );
    const html = await res.text();
    // CWS shows user count in various formats
    const patterns = [
      /(\d[\d,]+)\s*users/i,
      /"userCount"\s*:\s*"?(\d[\d,]+)/i,
      />(\d[\d,]+)\s*users</i,
    ];
    for (const pattern of patterns) {
      const match = html.match(pattern);
      if (match) {
        const count = parseInt(match[1].replace(/,/g, ''), 10);
        if (count > 0) {
          console.log(`  ${extensionId}: ${count} users`);
          return count;
        }
      }
    }
    console.log(`  ${extensionId}: no user count found in ${html.length} bytes`);
    return null;
  } catch (err) {
    console.log(`  ${extensionId}: fetch error: ${err.message}`);
    return null;
  }
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

  // Don't update if we couldn't fetch any stats
  if (!foundAny) {
    console.log('Could not fetch any extension stats, skipping update');
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
