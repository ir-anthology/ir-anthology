// Generates a sitemap from the prerendered HTML files in the build directory.
// Sitemap files are capped at 50,000 URLs by the spec; with more pages the
// output becomes a sitemap index (sitemap.xml) referencing sitemap-1.xml,
// sitemap-2.xml, ... Submit sitemap.xml to search engines either way.
import { readdirSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const BUILD_DIR = process.argv[2] ?? 'build';
const SITE_URL = (process.env.SITE_URL ?? 'https://ir.webis.de').replace(/\/$/, '');
const CHUNK_SIZE = Number(process.env.SITEMAP_CHUNK_SIZE ?? 45000);

function collectHtmlFiles(dir, files = []) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) {
			collectHtmlFiles(path, files);
		} else if (entry.name.endsWith('.html')) {
			files.push(path);
		}
	}
	return files;
}

function toUrlPath(file) {
	const rel = relative(BUILD_DIR, file).replaceAll('\\', '/');
	if (rel === '404.html') return null; // SPA fallback, not a page
	if (rel === 'index.html') return '/';
	return '/' + rel.replace(/\/index\.html$/, '').replace(/\.html$/, '');
}

function xmlEscape(s) {
	return s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;').replaceAll("'", '&apos;');
}

function urlset(paths) {
	const urls = paths.map((p) => `  <url><loc>${xmlEscape(SITE_URL + encodeURI(p))}</loc></url>`);
	return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`;
}

const paths = collectHtmlFiles(BUILD_DIR).map(toUrlPath).filter(Boolean).sort();

if (paths.length <= CHUNK_SIZE) {
	writeFileSync(join(BUILD_DIR, 'sitemap.xml'), urlset(paths));
	console.log(`sitemap.xml written (${paths.length} URLs)`);
} else {
	const indexEntries = [];
	for (let i = 0; i * CHUNK_SIZE < paths.length; i++) {
		const name = `sitemap-${i + 1}.xml`;
		writeFileSync(join(BUILD_DIR, name), urlset(paths.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE)));
		indexEntries.push(`  <sitemap><loc>${xmlEscape(`${SITE_URL}/${name}`)}</loc></sitemap>`);
	}
	const index = `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${indexEntries.join('\n')}\n</sitemapindex>\n`;
	writeFileSync(join(BUILD_DIR, 'sitemap.xml'), index);
	console.log(`sitemap index written (${paths.length} URLs in ${indexEntries.length} files)`);
}
