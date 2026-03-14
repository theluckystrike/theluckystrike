const fs = require('fs');

const EXTENSIONS = [
  { name: 'Tab Suspender Pro', id: 'ofgncemnlblfnocjbojdhamacfffcpnm' },
  { name: 'BeLikeNative', id: 'fphfgdknbpakeedbaenojjdcdoajihik' },
];

async function getExtensionStats(extensionId) {
  try {
    const res = await fetch(
      `https://chrome.google.com/webstore/detail/${extensionId}`
    );
    const html = await res.text();
    const userMatch = html.match(/(\d[\d,]+)\s*users/i);
    return userMatch ? parseInt(userMatch[1].replace(/,/g, ''), 10) : null;
  } catch {
    return null;
  }
}

async function main() {
  let totalUsers = 0;
  const stats = [];

  for (const ext of EXTENSIONS) {
    const users = await getExtensionStats(ext.id);
    if (users !== null) {
      totalUsers += users;
      stats.push(`${ext.name}: ${users.toLocaleString()} users`);
    }
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
