#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// 빌드 디렉토리 생성
const distDir = path.join(__dirname, 'dist');
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
}

// HTML 파일 복사
const srcHtml = path.join(__dirname, 'src', 'index.html');
const distHtml = path.join(distDir, 'index.html');

if (fs.existsSync(srcHtml)) {
    fs.copyFileSync(srcHtml, distHtml);
    console.log('✅ HTML 파일 복사 완료');
} else {
    console.error('❌ src/index.html 파일을 찾을 수 없습니다');
    process.exit(1);
}

// _redirects 파일 복사
const srcRedirects = path.join(__dirname, '_redirects');
const distRedirects = path.join(distDir, '_redirects');

if (fs.existsSync(srcRedirects)) {
    fs.copyFileSync(srcRedirects, distRedirects);
    console.log('✅ _redirects 파일 복사 완료');
}

// 빌드 정보 생성
const buildInfo = {
    timestamp: new Date().toISOString(),
    version: process.env.GITHUB_SHA || 'local',
    environment: process.env.NODE_ENV || 'development'
};

fs.writeFileSync(
    path.join(distDir, 'build-info.json'),
    JSON.stringify(buildInfo, null, 2)
);

console.log('🚀 빌드 완료!');
console.log(`📁 출력 디렉토리: ${distDir}`);
console.log(`⏰ 빌드 시간: ${buildInfo.timestamp}`);