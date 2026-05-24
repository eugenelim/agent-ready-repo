const fs = require('fs');
const path = require('path');

let MsgReader;
try {
  MsgReader = require('@nicecode/msg-reader').default || require('@nicecode/msg-reader');
} catch {
  MsgReader = require('msgreader').default || require('msgreader');
}

const filePath = process.argv[2];
if (!filePath) { console.error('Usage: node extract-attachments.js <file.msg>'); process.exit(1); }

const buf = fs.readFileSync(filePath);
const reader = new MsgReader(buf);
const msg = reader.getFileData();
const attachments = msg.attachments || [];

if (attachments.length === 0) {
  console.log('No attachments to extract.');
  process.exit(0);
}

const outDir = path.basename(filePath, '.msg') + '_attachments';
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

attachments.forEach((att, i) => {
  const name = att.fileName || att.name || ('attachment_' + (i + 1));
  const content = reader.getAttachment(i);
  if (content && content.content) {
    fs.writeFileSync(path.join(outDir, name), Buffer.from(content.content));
    console.log('EXTRACTED: ' + path.join(outDir, name));
  } else {
    console.log('SKIPPED (no content): ' + name);
  }
});
