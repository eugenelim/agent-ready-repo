const fs = require('fs');
const path = require('path');

let MsgReader;
try {
  MsgReader = require('@nicecode/msg-reader').default || require('@nicecode/msg-reader');
} catch {
  MsgReader = require('msgreader').default || require('msgreader');
}

const filePath = process.argv[2];
if (!filePath) { console.error('Usage: node convert.js <file.msg>'); process.exit(1); }

const buf = fs.readFileSync(filePath);
const reader = new MsgReader(buf);
const msg = reader.getFileData();

function htmlToMd(html) {
  if (!html) return '';
  let md = html;
  md = md.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  md = md.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  for (let i = 6; i >= 1; i--) {
    md = md.replace(new RegExp('<h' + i + '[^>]*>([\\s\\S]*?)<\\/h' + i + '>', 'gi'),
      (_, c) => '#'.repeat(i) + ' ' + c.replace(/<[^>]+>/g, '').trim() + '\n\n');
  }
  md = md.replace(/<(strong|b)>([\s\S]*?)<\/\1>/gi, '**$2**');
  md = md.replace(/<(em|i)>([\s\S]*?)<\/\1>/gi, '*$2*');
  md = md.replace(/<a\s+[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, '[$2]($1)');
  md = md.replace(/<ul[^>]*>([\s\S]*?)<\/ul>/gi, (_, inner) =>
    inner.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, (_, li) => '- ' + li.replace(/<[^>]+>/g, '').trim() + '\n') + '\n');
  let counter = 0;
  md = md.replace(/<ol[^>]*>([\s\S]*?)<\/ol>/gi, (_, inner) => {
    counter = 0;
    return inner.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi,
      (_, li) => (++counter) + '. ' + li.replace(/<[^>]+>/g, '').trim() + '\n') + '\n';
  });
  md = md.replace(/<table[^>]*>([\s\S]*?)<\/table>/gi, (_, tbl) => {
    const rows = [];
    let m, rm = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    while (m = rm.exec(tbl)) {
      const cells = [];
      let cm, cr = /<(td|th)[^>]*>([\s\S]*?)<\/\1>/gi;
      while (cm = cr.exec(m[1])) cells.push(cm[2].replace(/<[^>]+>/g, '').trim());
      rows.push(cells);
    }
    if (!rows.length) return '';
    const hdr = '| ' + rows[0].join(' | ') + ' |';
    const sep = '| ' + rows[0].map(() => '---').join(' | ') + ' |';
    const body = rows.slice(1).map(r => '| ' + r.join(' | ') + ' |').join('\n');
    return '\n' + hdr + '\n' + sep + '\n' + body + '\n\n';
  });
  md = md.replace(/<br\s*\/?>/gi, '\n');
  md = md.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, '$1\n\n');
  md = md.replace(/<div[^>]*>([\s\S]*?)<\/div>/gi, '$1\n');
  md = md.replace(/<[^>]+>/g, '');
  md = md.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
    .replace(/&#\d+;/g, '');
  return md.replace(/\n{3,}/g, '\n\n').trim();
}

let md = '';
md += '# ' + (msg.subject || 'No Subject') + '\n\n';
md += '| Field | Value |\n';
md += '| --- | --- |\n';
md += '| **From** | ' + (msg.senderName || '') + (msg.senderEmail ? ' <' + msg.senderEmail + '>' : '') + ' |\n';

const toRecipients = (msg.recipients || []).filter(r => r.recipType === 'to' || r.recipType === 1 || !r.recipType);
const ccRecipients = (msg.recipients || []).filter(r => r.recipType === 'cc' || r.recipType === 2);
const bccRecipients = (msg.recipients || []).filter(r => r.recipType === 'bcc' || r.recipType === 3);

function formatRecipients(list) {
  return list.map(r => (r.name || '') + (r.email ? ' <' + r.email + '>' : '')).join('; ') || '\u2014';
}

md += '| **To** | ' + formatRecipients(toRecipients.length ? toRecipients : msg.recipients || []) + ' |\n';
if (ccRecipients.length) md += '| **CC** | ' + formatRecipients(ccRecipients) + ' |\n';
if (bccRecipients.length) md += '| **BCC** | ' + formatRecipients(bccRecipients) + ' |\n';

const dateStr = msg.messageDeliveryTime || msg.clientSubmitTime || msg.creationTime || '';
if (dateStr) md += '| **Date** | ' + dateStr + ' |\n';
if (msg.importance && msg.importance !== 'normal' && msg.importance !== 1) {
  md += '| **Importance** | ' + msg.importance + ' |\n';
}

md += '\n---\n\n';

let body = '';
if (msg.htmlBody || msg.html) {
  body = htmlToMd(msg.htmlBody || msg.html);
} else if (msg.body) {
  body = msg.body;
}

md += body ? body + '\n\n' : '*No message body found.*\n\n';

const attachments = msg.attachments || [];
if (attachments.length > 0) {
  md += '---\n\n';
  md += '## Attachments\n\n';
  md += '| # | Filename | Size | Type |\n';
  md += '| --- | --- | --- | --- |\n';
  attachments.forEach((att, i) => {
    const name = att.fileName || att.name || 'unnamed';
    const ext = path.extname(name).toLowerCase();
    const size = att.contentLength || att.dataSize || att.content?.length || '\u2014';
    const sizeStr = typeof size === 'number'
      ? (size > 1048576 ? (size / 1048576).toFixed(1) + ' MB'
        : size > 1024 ? (size / 1024).toFixed(1) + ' KB'
        : size + ' B')
      : String(size);
    const isInline = att.contentId || att.isInline ? ' (inline)' : '';
    md += '| ' + (i + 1) + ' | ' + name + isInline + ' | ' + sizeStr + ' | ' + (ext || '\u2014') + ' |\n';
  });
  md += '\n';
}

const embeddedMsgs = attachments.filter(a =>
  (a.fileName || a.name || '').toLowerCase().endsWith('.msg') || a.attachmentType === 'msg'
);
if (embeddedMsgs.length > 0) {
  md += '> **Note:** This email contains ' + embeddedMsgs.length + ' embedded message(s). ';
  md += 'Run this skill on the extracted .msg file(s) to convert them as well.\n\n';
}

const outFile = path.basename(filePath).replace(/\.msg$/i, '') + '.md';
fs.writeFileSync(outFile, md);

const summary = {
  subject: msg.subject || 'No Subject',
  from: msg.senderName || msg.senderEmail || 'Unknown',
  to: formatRecipients(toRecipients.length ? toRecipients : msg.recipients || []),
  date: dateStr || 'Unknown',
  hasHtmlBody: !!(msg.htmlBody || msg.html),
  hasPlainBody: !!msg.body,
  bodyLength: body.length,
  attachmentCount: attachments.length,
  embeddedMsgCount: embeddedMsgs.length,
  ccCount: ccRecipients.length,
  bccCount: bccRecipients.length
};

console.log('WROTE: ' + outFile);
console.log('SUMMARY: ' + JSON.stringify(summary));
