#!/usr/bin/env pwsh
<#
.SYNOPSIS
Push Focus Guard repository to GitHub

.DESCRIPTION
Interactive script to configure GitHub remote and push the Focus Guard project

.EXAMPLE
.\push-to-github.ps1
#>

Write-Host "`n" -ForegroundColor Green
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Focus Guard - GitHub Push Setup                      ║" -ForegroundColor Cyan
Write-Host "║   v1.0.0 - Production Ready                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
$hasGitHub = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

if ($hasGitHub) {
    Write-Host "✓ GitHub CLI detected" -ForegroundColor Green
    Write-Host ""
    Write-Host "Would you like to authenticate and create the repository automatically?" -ForegroundColor Yellow
    Write-Host "[1] Yes, use GitHub CLI (automatic)" -ForegroundColor Green
    Write-Host "[2] No, use HTTPS URL (manual)" -ForegroundColor Gray
    $choice = Read-Host "Select option (1-2)"
    
    if ($choice -eq "1") {
        Write-Host ""
        Write-Host "🔐 Logging in to GitHub..." -ForegroundColor Yellow
        try {
            gh auth login -p https --web
            Write-Host "✓ GitHub authentication successful" -ForegroundColor Green
            Write-Host ""
            
            $repoName = "focus-guard-ai-pomodoro"
            Write-Host "📦 Creating repository '$repoName'..." -ForegroundColor Yellow
            gh repo create $repoName --public --source=. --remote=origin --push
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "✅ SUCCESS! Repository created and pushed to GitHub" -ForegroundColor Green
                Write-Host ""
                Write-Host "Repository URL: https://github.com/$(gh api user -q '.login')/$repoName" -ForegroundColor Cyan
                exit 0
            }
            else {
                Write-Host "⚠️  Repository might already exist. Proceeding with manual push..." -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "⚠️  Error with GitHub CLI: $_" -ForegroundColor Yellow
            Write-Host "Proceeding with manual setup..." -ForegroundColor Yellow
        }
    }
}

# Manual setup
Write-Host ""
Write-Host "📋 Manual GitHub Setup" -ForegroundColor Yellow
Write-Host ""
Write-Host "Step 1: Create new repository on GitHub" -ForegroundColor Cyan
Write-Host "  1. Go to https://github.com/new" -ForegroundColor Gray
Write-Host "  2. Enter repository name: focus-guard-ai-pomodoro" -ForegroundColor Gray
Write-Host "  3. Add description: AI-powered Pomodoro timer with focus detection" -ForegroundColor Gray
Write-Host "  4. Choose Public (for open-source)" -ForegroundColor Gray
Write-Host "  5. DO NOT initialize with README, .gitignore, or license" -ForegroundColor Gray
Write-Host "  6. Click 'Create repository'" -ForegroundColor Gray
Write-Host ""

$githubUrl = Read-Host "Paste your GitHub repository URL (https://github.com/...)"

if ([string]::IsNullOrWhiteSpace($githubUrl)) {
    Write-Host "❌ Error: No URL provided" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔗 Setting up remote..." -ForegroundColor Yellow

try {
    # Check if remote already exists
    $remoteExists = git remote get-url origin -ErrorAction SilentlyContinue
    
    if ($remoteExists) {
        Write-Host "⚠️  Remote 'origin' already exists, removing..." -ForegroundColor Yellow
        git remote remove origin
    }
    
    # Add remote
    git remote add origin $githubUrl
    Write-Host "✓ Remote configured: $githubUrl" -ForegroundColor Green
    
    # Rename branch to main if on master
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -eq "master") {
        Write-Host ""
        Write-Host "🔄 Renaming branch master → main..." -ForegroundColor Yellow
        git branch -M main
        Write-Host "✓ Branch renamed" -ForegroundColor Green
    }
    
    # Push to GitHub
    Write-Host ""
    Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
    Write-Host "(This may take a moment...)" -ForegroundColor Gray
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║   ✅ SUCCESS! Project pushed to GitHub                 ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "📍 Repository URL:" -ForegroundColor Cyan
        Write-Host "   $githubUrl" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔍 Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Visit your repository on GitHub" -ForegroundColor Gray
        Write-Host "  2. Add repository topics: pomodoro, ai, productivity" -ForegroundColor Gray
        Write-Host "  3. Enable GitHub Pages for documentation" -ForegroundColor Gray
        Write-Host "  4. Add release notes for v1.0.0" -ForegroundColor Gray
        Write-Host "  5. Share repository link with collaborators" -ForegroundColor Gray
        Write-Host ""
    }
    else {
        Write-Host ""
        Write-Host "❌ Error pushing to GitHub" -ForegroundColor Red
        Write-Host "Please check your credentials and try again" -ForegroundColor Red
        exit 1
    }
    
}
catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Commands for future use:" -ForegroundColor Yellow
Write-Host "  git push              # Push changes" -ForegroundColor Gray
Write-Host "  git pull              # Pull changes" -ForegroundColor Gray
Write-Host "  git log --oneline     # View history" -ForegroundColor Gray
Write-Host ""
