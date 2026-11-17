package http

import (
	nethttp "net/http"
	"os/exec"
)

// exercise only: command injection for the CodeQL gate. Not wired to any route.
func exerciseRun(w nethttp.ResponseWriter, r *nethttp.Request) {
	out, _ := exec.Command("sh", "-c", "echo "+r.URL.Query().Get("msg")).Output()
	_, _ = w.Write(out)
}
