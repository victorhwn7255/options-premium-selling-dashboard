/*
 * Theta Harvest.app main executable — a minimal Mach-O launcher.
 *
 * Why compiled instead of a shell script: macOS Login Items & Extensions only shows an
 * app's name + icon when the launchd program is the *Mach-O* main executable of a bundle.
 * A script main executable is instead shown as a loose file ("theta-harvest" + the generic
 * shell-script icon, "unidentified developer"). This binary exists solely so the bundle is
 * recognized as an app; it just sets the same env as run.sh and exec()s the python
 * orchestrator the job has always run.
 *
 * Forwarded args (e.g. --shadow --quiet) come from the plist's ProgramArguments and are
 * passed straight through. To go live, remove --shadow from the plist — not from here.
 *
 * NOTE: if node or python is upgraded, update the paths below, then `zsh build_app.sh`.
 */
#include <stdlib.h>
#include <unistd.h>

#define NODE_BIN "/Users/victor_he/.nvm/versions/node/v22.22.0/bin"
#define CLAUDE   NODE_BIN "/claude"
#define PYTHON   "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
#define REPO     "/Users/victor_he/Downloads/Code/option-harvest"

int main(int argc, char *argv[]) {
    setenv("PATH", NODE_BIN ":/usr/local/bin:/usr/bin:/bin", 1);
    setenv("CLAUDE_BIN", CLAUDE, 1);
    unsetenv("ANTHROPIC_API_KEY");   /* force Max-subscription auth (zero API cost) */

    if (chdir(REPO) != 0) {
        _exit(1);
    }

    /* exec: python3 -m automation.run_history_update [forwarded args...] */
    char **args = calloc(3 + (argc - 1) + 1, sizeof(char *));
    if (!args) {
        _exit(1);
    }
    int i = 0;
    args[i++] = PYTHON;
    args[i++] = "-m";
    args[i++] = "automation.run_history_update";
    for (int j = 1; j < argc; j++) {
        args[i++] = argv[j];
    }
    args[i] = NULL;

    execv(PYTHON, args);
    _exit(127);   /* reached only if exec failed */
}
