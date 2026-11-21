# Run from a local checkout after `gh auth login` with repository write/admin access.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repository = 'DaoNgocDinh/BlockChain_MiniVoting'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is required. Install it, then run gh auth login and gh auth setup-git.'
}

function Invoke-GitHubJson {
    param([string[]]$ApiArguments, [object]$Body = $null)
    $temporaryFile = $null
    try {
        $arguments = @('api') + $ApiArguments
        if ($null -ne $Body) {
            $temporaryFile = Join-Path ([IO.Path]::GetTempPath()) ('minivoting-' + [guid]::NewGuid().ToString('N') + '.json')
            $json = ConvertTo-Json -InputObject $Body -Depth 30
            [IO.File]::WriteAllText($temporaryFile, $json, (New-Object System.Text.UTF8Encoding($false)))
            $arguments += @('--input', $temporaryFile)
        }
        $response = & gh @arguments
        if ($LASTEXITCODE -ne 0) { throw ('GitHub API operation failed: ' + ($ApiArguments -join ' ')) }
        if ($response) { return (($response -join "`n") | ConvertFrom-Json) }
    } finally {
        if ($temporaryFile -and (Test-Path -LiteralPath $temporaryFile)) {
            Remove-Item -LiteralPath $temporaryFile
        }
    }
}

function Get-PagedItems {
    param([string]$Endpoint)
    $pages = Invoke-GitHubJson -ApiArguments @($Endpoint, '--paginate', '--slurp')
    foreach ($page in $pages) { foreach ($item in $page) { $item } }
}

Push-Location $projectRoot
try {
    & gh auth status --hostname github.com
    if ($LASTEXITCODE -ne 0) { throw 'Sign in with gh auth login before running setup.' }
    & gh auth setup-git --hostname github.com
    if ($LASTEXITCODE -ne 0) { throw 'Could not configure authenticated Git access.' }
    $branch = & git branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'Run setup from local main.' }
    $dirty = & git status --porcelain
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Commit or preserve working changes before setup; no automatic stash/reset is performed.' }
    $remoteUrl = & git remote get-url origin
    if ($LASTEXITCODE -ne 0 -or $remoteUrl -notmatch '^https://github\.com/DaoNgocDinh/BlockChain_MiniVoting(?:\.git)?/?$') {
        throw 'origin does not match the intended repository.'
    }

    # A normal push refuses divergent history and active protections. Never force.
    & git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw 'Initial push failed. Inspect the remote history or existing protection before retrying.' }

    $rulesetBody = Get-Content -LiteralPath '.github/rulesets/protect-main.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    $rulesets = @(Get-PagedItems -Endpoint "repos/$repository/rulesets?per_page=100")
    $matchingRulesets = @($rulesets | Where-Object { $_.name -eq 'protect-main' })
    if ($matchingRulesets.Count -gt 1) { throw 'Multiple protect-main rulesets exist; review them manually before setup.' }
    if ($matchingRulesets.Count -eq 0) {
        $null = Invoke-GitHubJson -ApiArguments @('--method', 'POST', "repos/$repository/rulesets") -Body $rulesetBody
    } else {
        # Preserve an existing rule rather than silently weakening it or removing bypasses.
        Write-Output 'Existing protect-main ruleset found; preserving it and verifying below.'
    }
    $activeRules = @(Invoke-GitHubJson -ApiArguments @("repos/$repository/rules/branches/main"))
    $pullRequestRules = @($activeRules | Where-Object { $_.type -eq 'pull_request' -and $_.parameters.required_approving_review_count -ge 1 -and $_.parameters.required_review_thread_resolution })
    if (-not $pullRequestRules -or -not ($activeRules | Where-Object type -eq 'deletion') -or -not ($activeRules | Where-Object type -eq 'non_fast_forward')) {
        throw 'Active main protection is missing required review/thread/deletion/force-push rules. Inspect Settings > Rules > Rulesets.'
    }
    Write-Output 'Verified active main protection.'

    $metadata = Get-Content -LiteralPath '.github/project-metadata.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    $labels = @(Get-PagedItems -Endpoint "repos/$repository/labels?per_page=100")
    foreach ($label in $metadata.labels) {
        if (-not ($labels | Where-Object { $_.name -eq $label.name })) {
            $null = Invoke-GitHubJson -ApiArguments @('--method', 'POST', "repos/$repository/labels") -Body $label
        }
    }
    $milestones = @(Get-PagedItems -Endpoint "repos/$repository/milestones?state=all&per_page=100")
    $milestoneNumbers = @{}
    foreach ($milestone in $metadata.milestones) {
        $existing = @($milestones | Where-Object { $_.title -eq $milestone.title })
        if ($existing.Count -gt 1) { throw ('Duplicate milestone: ' + $milestone.title) }
        if ($existing.Count -eq 0) {
            $created = Invoke-GitHubJson -ApiArguments @('--method', 'POST', "repos/$repository/milestones") -Body $milestone
            $milestoneNumbers[$milestone.title] = $created.number
        } else { $milestoneNumbers[$milestone.title] = $existing[0].number }
    }

    $definitions = Get-Content -LiteralPath 'docs/backlog.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    $existingIssues = @(Get-PagedItems -Endpoint "repos/$repository/issues?state=all&per_page=100")
    $issueNumbers = @{}
    foreach ($definition in $definitions) {
        $marker = '<!-- minivoting:' + $definition.key + ' -->'
        $matchesForTask = @($existingIssues | Where-Object { -not $_.pull_request -and $_.body -and $_.body.Contains($marker) })
        if ($matchesForTask.Count -gt 1) { throw ('Duplicate task marker: ' + $definition.key) }
        if ($matchesForTask.Count -eq 1) {
            $issueNumbers[$definition.key] = $matchesForTask[0].number
            Write-Output ('Preserved existing issue #' + $matchesForTask[0].number + ' for ' + $definition.key)
            continue
        }
        $dependencies = @($definition.dependencies | ForEach-Object {
            if (-not $issueNumbers.ContainsKey($_)) { throw ('Missing earlier dependency: ' + $_) }
            '#' + $issueNumbers[$_] + ' (' + $_ + ')'
        })
        $bodyLines = @($marker, '', ('Phu trach: **TV' + $definition.member + '**. Moc: **W' + $definition.week + '**.'),
            ('Review: ' + $definition.reviewer), ('Ban giao: ' + $definition.files),
            ('Phu thuoc: ' + $(if ($dependencies.Count) { $dependencies -join ', ' } else { 'Khong' })),
            '', 'Nguon: docs/ke-hoach.md, muc 12-17 va 20. Chua chot ngay bat dau/deadline.', '', '### Cong viec', '')
        $bodyLines += @($definition.scope | ForEach-Object { '- ' + $_ })
        $bodyLines += @('', '### Tieu chi nghiem thu', '')
        $bodyLines += @($definition.acceptance | ForEach-Object { '- [ ] ' + $_ })
        $bodyLines += @('', '### Definition of Done', '', 'PR lien ket issue; test phu hop dat; cap nhat docs; co nguoi khac review va demo trong ban nhom. Moi nguoi viet chuong bao cao phan minh.')
        $area = @('core', 'consensus', 'network-storage', 'frontend')[$definition.member - 1]
        $priority = if ($definition.member -le 3 -and $definition.week -le 4) { 'priority:critical' } else { 'priority:normal' }
        $taskLabels = @('type:task', ('owner:tv' + $definition.member), ('area:' + $area), $priority)
        if ($definition.member -eq 4 -and $definition.week -eq 4) { $taskLabels += 'area:testing' }
        if ($definition.member -eq 4 -and $definition.week -eq 5) { $taskLabels += 'area:experiments' }
        if ($definition.week -ge 5) { $taskLabels += 'area:docs' }
        $milestoneTitle = $metadata.milestones[$definition.week - 1].title
        $issueBody = @{ title = $definition.title; body = $bodyLines -join "`n"; labels = $taskLabels; milestone = $milestoneNumbers[$milestoneTitle] }
        if ($definition.member -eq 4) { $issueBody.assignees = @('DaoNgocDinh') }
        $created = Invoke-GitHubJson -ApiArguments @('--method', 'POST', "repos/$repository/issues") -Body $issueBody
        $issueNumbers[$definition.key] = $created.number
        Write-Output ('Created #' + $created.number + ': ' + $definition.title)
    }

    if ($issueNumbers.Count -ne 24) { throw 'Expected exactly 24 tracked tasks.' }
    Write-Output 'Verified 24 task mappings, 6 milestones and active main protection.'
    Write-Output "https://github.com/$repository/issues"
    Write-Output 'After both CI jobs pass, add their status checks to the ruleset. Assign TV1-TV3 after the real usernames accept collaborator invitations.'
} finally { Pop-Location }
