from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

game = Path.home() / "FootballArena3D" / "index.html"
if not game.is_file():
    sys.exit("ERROR: index.html not found. Nothing changed.")

src = game.read_text(encoding="utf-8")
marker = "ARENA_SCORE_CAMERA_CONTROL_MARKER_V1"

if marker in src:
    sys.exit("This upgrade is already installed. Nothing changed.")

# Insert into the same inline script as the game code.
insert_at = None
for match in re.finditer(r"</script\s*>", src, re.I):
    start = src.rfind("<script", 0, match.start())
    if start >= 0:
        segment = src[start:match.start()]
        if "function movePlayer(" in segment:
            insert_at = match.start()

if insert_at is None:
    sys.exit(
        "ERROR: Could not locate the game script containing movePlayer(). "
        "No changes made."
    )

backup = game.with_name(
    "index_backup_ui_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".html"
)
shutil.copy2(game, backup)

patch = r"""
/* ARENA_SCORE_CAMERA_CONTROL_MARKER_V1 */
(function arenaScoreCameraControlUpgrade() {
  const style = document.createElement("style");
  style.textContent = `
    #arena-tv-score {
      position: fixed !important;
      top: max(10px, env(safe-area-inset-top)) !important;
      left: max(10px, env(safe-area-inset-left)) !important;
      right: auto !important;
      bottom: auto !important;
      transform: none !important;
      z-index: 10000 !important;
      max-width: min(78vw, 330px) !important;
      box-sizing: border-box !important;
      padding: 11px 15px !important;
      border: 1px solid rgba(255,255,255,.35) !important;
      border-left: 4px solid #53e3a5 !important;
      border-radius: 8px !important;
      background: rgba(8,18,27,.94) !important;
      color: #fff !important;
      font: 700 17px/1.35 system-ui, sans-serif !important;
      letter-spacing: .5px !important;
      text-align: left !important;
      box-shadow: 0 4px 18px rgba(0,0,0,.3) !important;
      pointer-events: none !important;
    }
  `;
  document.head.appendChild(style);

  function findScoreboard() {
    const candidates = [...document.querySelectorAll("body *")].filter(el => {
      if (!el || el.id === "arena-tv-score") return false;
      const text = (el.innerText || "").trim();
      return /\bYOU\b/i.test(text) && /\bCPU\b/i.test(text) &&
             text.length < 100;
    });

    // Prefer the smallest container that includes both team labels.
    candidates.sort((a, b) =>
      (a.innerText || "").length - (b.innerText || "").length
    );
    return candidates[0] || null;
  }

  function styleScoreboard() {
    let el = document.getElementById("arena-tv-score");
    if (!el) {
      const old = findScoreboard();
      if (!old) return;

      // Move the existing scoreboard node so its score updates remain live.
      el = old;
      el.id = "arena-tv-score";
    }

    // Change labels in text nodes only; preserve score and timer elements.
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    for (const node of nodes) {
      if (!node.nodeValue) continue;
      node.nodeValue = node.nodeValue
        .replace(/\bYOU\b/gi, "TEAM A")
        .replace(/\bCPU\b/gi, "TEAM B");
    }
  }

  styleScoreboard();
  const observer = new MutationObserver(() => styleScoreboard());
  observer.observe(document.body, {
    childList: true, subtree: true, characterData: true
  });

  let marker = null;
  let markerScene = null;
  let cameraAdjusted = false;

  function getPlayerGroup(player) {
    return player && player.g && player.g.position ? player.g : null;
  }

  function tick() {
    try {
      // Add a bright ring around the human-controlled player.
      if (typeof you !== "undefined" && typeof scene !== "undefined") {
        const group = getPlayerGroup(you);

        if (group && (!marker || markerScene !== scene)) {
          if (marker && marker.parent) marker.parent.remove(marker);

          marker = new THREE.Mesh(
            new THREE.RingGeometry(0.27, 0.39, 28),
            new THREE.MeshBasicMaterial({
              color: 0xfff23d,
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.98,
              depthWrite: false
            })
          );
          marker.rotation.x = -Math.PI / 2;
          marker.renderOrder = 20;
          markerScene = scene;
          scene.add(marker);
        }

        if (marker && group) {
          marker.position.set(
            group.position.x,
            group.position.y + 0.035,
            group.position.z
          );
          const pulse = 1 + Math.sin(performance.now() * 0.006) * 0.045;
          marker.scale.set(pulse, pulse, pulse);
        }
      }

      // A slightly wider field of view can show more of the pitch.
      if (!cameraAdjusted && typeof camera !== "undefined" &&
          camera && camera.isPerspectiveCamera) {
        camera.fov = Math.max(camera.fov || 50, 60);
        camera.updateProjectionMatrix();
        cameraAdjusted = true;
      }
    } catch (err) {
      // Avoid breaking the original game's animation if a variable differs.
    }

    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
})();
"""

updated = src[:insert_at] + patch + "\n" + src[insert_at:]
if marker not in updated:
    sys.exit("ERROR: Patch verification failed. Original game is unchanged.")

tmp = game.with_name("index.html.ui_tmp")
tmp.write_text(updated, encoding="utf-8")
tmp.replace(game)

print("SUCCESS: Scoreboard, controlled-player ring, and camera patch installed.")
print("Backup:", backup.name)
print("Refresh Chrome to test.")
