# Deploying pDST-calc on ABC-cluster

The app ships as a container and deploys via the `abc app` command. It is also
runnable as a plain Docker container anywhere.

## Run locally (Docker)

```bash
docker build -t pdst-calc:poc .
docker run --rm -p 3838:3838 pdst-calc:poc
# open http://localhost:3838
```

## Deploy on ABC-cluster (`abc app`)

Apps are bring-your-own-image: build the image on the cluster build host, tag it
for the local image store, then deploy the included `abc-app.yaml`.

```bash
# on the build host
docker build -t pdst-calc:poc .
docker tag  pdst-calc:poc aither.local/pdst-calc:poc

# deploy (abc-apps namespace, routed at <project>-<name>.apps.<tier>…)
abc app deploy
abc app show pdst-calc
```

Live instance: <https://genpath-pdst-calc.apps.seedling.abc-cluster.cloud>

## Notes

- **Framework:** Shiny for Python, served at `/` on port `3838` (WebSocket passes
  through the edge for interactivity).
- **State:** the app's SQLite DB (`dstcalc.db`) + bcrypt auth are created inside
  the container and are **ephemeral** — they reset on redeploy/restart. Mount a
  volume (or wire persistent storage) if you need accounts/data to survive.
- **Resources:** defaults to 1000 MHz / 2048 MiB (`abc-app.yaml`); tune as needed.
