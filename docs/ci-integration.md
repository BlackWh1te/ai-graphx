# .github/workflows/graphx-ci.yml

name: GraphX Architectural Audit

on:
  pull_request:
    branches: [ main ]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install GraphX
      run: |
        pip install ai-graphx
        
    - name: Generate Baseline Graph (Main)
      run: |
        git checkout main
        python -m graphx index .
        mv graphx-out/graph.json baseline.json

    - name: Generate Current Graph (PR)
      run: |
        git checkout ${{ github.head_ref }}
        python -m graphx index .
        mv graphx-out/graph.json current.json

    - name: Audit Structural Changes
      id: audit
      run: |
        python -m graphx ci baseline.json current.json > report.md
        cat report.md >> $GITHUB_STEP_SUMMARY

    - name: Post PR Comment
      uses: actions/github-script@v6
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        script: |
          const fs = require('fs');
          const report = fs.readFileSync('report.md', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: report
          })
