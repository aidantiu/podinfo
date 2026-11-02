package main

// EXERCISE ONLY (PR "bad ingredient is blocked"): pulls an old go-git with fixable
// CRITICAL vulnerabilities into the binary so that both the source scan (sca) and
// the image scan (build) have something to find. Never merge.
import _ "github.com/go-git/go-git/v5"
