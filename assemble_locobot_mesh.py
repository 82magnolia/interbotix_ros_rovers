#!/usr/bin/env python3
"""
assemble_locobot_mesh.py

Assembles the LoCoBot URDF mesh components into a single merged .ply file.
Reads mesh files directly from the interbotix_xslocobot_descriptions package
without requiring a ROS installation.

All revolute/prismatic/continuous joints are placed at their zero pose
(origin offset only, no rotation). The resulting mesh is a static snapshot
of the robot in its default configuration.

Usage:
    python assemble_locobot_mesh.py \\
        --base-model kobuki --arm-model mobile_px100

For the full option list:
    python assemble_locobot_mesh.py --help
"""

import argparse
import math
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import trimesh
except ImportError:
    print(
        "Error: trimesh is not installed. Run:  pip install trimesh",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------

PI = math.pi


def rpy_to_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Convert URDF-convention RPY angles to a 3x3 rotation matrix.

    URDF uses extrinsic XYZ rotations: R = Rz(yaw) @ Ry(pitch) @ Rx(roll)
    """
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    Rx = np.array([[1, 0, 0],
                   [0, cr, -sr],
                   [0, sr, cr]])
    Ry = np.array([[cp, 0, sp],
                   [0, 1, 0],
                   [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0],
                   [sy, cy, 0],
                   [0, 0, 1]])
    return Rz @ Ry @ Rx


def make_tf(
    xyz: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rpy: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> np.ndarray:
    """Build a 4x4 homogeneous transformation matrix from xyz and RPY."""
    tf = np.eye(4)
    tf[:3, :3] = rpy_to_matrix(*rpy)
    tf[:3, 3] = xyz
    return tf


# ---------------------------------------------------------------------------
# Kinematic tree builder
# ---------------------------------------------------------------------------

# Fields: (rel_path, link_world_tf, vis_xyz, vis_rpy, scale)
_Entry = Tuple[str, np.ndarray, tuple, tuple, float]


def _build_entries(
    base_model: str,
    arm_model: str,
    show_lidar: bool,
    show_gripper_bar: bool,
    show_gripper_fingers: bool,
) -> List[_Entry]:
    """Return mesh entries with their world-space transforms.

    All transforms come directly from the URDF/xacro source files.
    Joint variables are held at zero (only the <origin> offset applies).
    """
    entries: List[_Entry] = []

    def add(
        rel_path,
        link_tf,
        vis_xyz=(0, 0, 0),
        vis_rpy=(0, 0, 0),
        scale=0.001,
    ):
        entries.append((rel_path, link_tf, vis_xyz, vis_rpy, scale))

    tower_size = "large" if arm_model == "mobile_wx250s" else "small"

    # ─────────────────────────── BASE ────────────────────────────────────
    # base_footprint is the world origin (identity).

    if base_model == "kobuki":
        # base_joint: base_footprint → base_link  xyz=(0, 0, 0.0102)
        tf_base = make_tf(xyz=(0, 0, 0.0102))

        # Kobuki body (DAE, already in metres — scale=1)
        add(
            "locobot_meshes/kobuki_version/kobuki.dae",
            tf_base,
            vis_xyz=(0.001, 0, 0.05199),
            scale=1.0,
        )

        # Left wheel  joint rpy=(-pi/2,0,0) xyz=(0, 0.115, 0.025)
        tf_lw = tf_base @ make_tf(
            xyz=(0, 0.115, 0.025), rpy=(-PI / 2, 0, 0)
        )
        add(
            "locobot_meshes/kobuki_version/kobuki_wheel.dae",
            tf_lw,
            scale=1.0,
        )

        # Right wheel  joint rpy=(-pi/2,0,0) xyz=(0, -0.115, 0.025)
        tf_rw = tf_base @ make_tf(
            xyz=(0, -0.115, 0.025), rpy=(-PI / 2, 0, 0)
        )
        add(
            "locobot_meshes/kobuki_version/kobuki_wheel.dae",
            tf_rw,
            scale=1.0,
        )

        # plate joint: base_link → plate_link  xyz=(0, 0, 0.08825)
        tf_plate = tf_base @ make_tf(xyz=(0, 0, 0.08825))

    elif base_model == "create3":
        # base_joint: base_footprint → base_link  xyz=(0,0,0) (identity)
        tf_base = make_tf()

        # body_visual.dae is from the external 'irobot_create_description'
        # package and is not bundled with interbotix_xslocobot_descriptions.
        print(
            "  [note] Skipping Create3 body (body_visual.dae) — it lives"
            " in the external 'irobot_create_description' package.\n"
            "         All interbotix_xslocobot_descriptions meshes are"
            " included."
        )

        # bump_caster  joint xyz=(-0.1098, 0, 0.009648) rpy=(pi, 0, pi/2)
        tf_bump = tf_base @ make_tf(
            xyz=(-0.1098, 0, 0.009648), rpy=(PI, 0, PI / 2)
        )
        add("locobot_meshes/create3_version/bump_caster.stl", tf_bump)

        # plate joint: base_link → plate_link  xyz=(0, 0, 0.0934)
        tf_plate = tf_base @ make_tf(xyz=(0, 0, 0.0934))

    else:
        raise ValueError(
            f"Unknown base_model {base_model!r}. "
            "Choose 'kobuki' or 'create3'."
        )

    # plate_link mesh
    add(
        f"locobot_meshes/{base_model}_version/locobot_base_plate.stl",
        tf_plate,
    )

    # battery joint: plate_link → battery_link
    bat_xyz = (
        (-0.007, 0, 0.0125)
        if base_model == "kobuki"
        else (-0.0345, 0, 0.010763)
    )
    tf_battery = tf_plate @ make_tf(xyz=bat_xyz)
    add("locobot_meshes/locobot_battery.stl", tf_battery)

    # ─────────────── CAMERA TOWER ─────────────────────────────────────────
    # camera_tower joint: base_link → camera_tower_link
    ct_xyz = (
        (-0.023997, -0.000044, 0.08823)
        if base_model == "kobuki"
        else (-0.048271, 0, 0.10087)
    )
    tf_ct = tf_base @ make_tf(xyz=ct_xyz)
    add(
        "locobot_meshes/"
        f"{base_model}_version/locobot_camera_tower_{tower_size}.stl",
        tf_ct,
    )

    # pan joint origin (relative to camera_tower_link)
    _pan_xyz = {
        ("kobuki", "large"): (0.047228, 0, 0.44425),
        ("kobuki", "small"): (0.047228, 0, 0.38425),
        ("create3", "large"): (0.061228, 0, 0.462),
        ("create3", "small"): (0.061228, 0, 0.402),
    }
    tf_pan = tf_ct @ make_tf(xyz=_pan_xyz[(base_model, tower_size)])
    add("locobot_meshes/locobot_pan.stl", tf_pan, vis_rpy=(0, 0, PI / 2))

    # tilt joint: pan_link → tilt_link  xyz=(0.025034, 0, 0.019)
    tf_tilt = tf_pan @ make_tf(xyz=(0.025034, 0, 0.019))
    add("locobot_meshes/locobot_tilt.stl", tf_tilt, vis_rpy=(0, 0, PI / 2))

    # camera joint: tilt_link → camera_link  xyz=(0.05318, 0.0175, 9e-6)
    tf_cam = tf_tilt @ make_tf(xyz=(0.05318, 0.0175, 9e-6))
    add("locobot_meshes/locobot_camera.stl", tf_cam)

    # ─────────────── LIDAR ────────────────────────────────────────────────
    if show_lidar:
        _lidar_xyz = {
            ("kobuki", "large"): (-0.074, 0, 0.44425),
            ("kobuki", "small"): (-0.074, 0, 0.38425),
            ("create3", "large"): (-0.066095, 0, 0.462),
            ("create3", "small"): (-0.066095, 0, 0.402),
        }
        tf_lidar_tower = tf_ct @ make_tf(
            xyz=_lidar_xyz[(base_model, tower_size)]
        )
        add("locobot_meshes/locobot_lidar_tower.stl", tf_lidar_tower)

        # lidar joint: lidar_tower_link → laser_frame_link
        # xyz=(0, 0, 0.09425) rpy=(0, 0, pi)
        tf_lidar = tf_lidar_tower @ make_tf(
            xyz=(0, 0, 0.09425), rpy=(0, 0, PI)
        )
        add("locobot_meshes/locobot_lidar.stl", tf_lidar)

    # ─────────────────────────── ARM ─────────────────────────────────────
    if arm_model == "mobile_base":
        return entries

    # arm_cradle (wx200 only): camera_tower_link → arm_cradle_link
    if arm_model == "mobile_wx200":
        cradle_xyz = (
            (0.0215, 0, 0.1195)
            if base_model == "kobuki"
            else (0.037943, 0, 0.139)
        )
        tf_cradle = tf_ct @ make_tf(xyz=cradle_xyz)
        add("locobot_meshes/locobot_arm_cradle.stl", tf_cradle)

    # arm_stand (create3 only): plate_link → arm_stand_link → arm_base_link
    if base_model == "create3":
        tf_arm_stand = tf_plate @ make_tf(xyz=(0.092002, 0, 0.007763))
        add(
            "locobot_meshes/create3_version/locobot_arm_stand.stl",
            tf_arm_stand,
            scale=1.0,
        )
        tf_arm_base = tf_arm_stand @ make_tf(xyz=(0, 0, 0.023))
    else:
        arm_base_x = 0.111126 if arm_model == "mobile_px100" else 0.097277
        tf_arm_base = tf_plate @ make_tf(xyz=(arm_base_x, 0, 0.0095))

    # ─── px100 ────────────────────────────────────────────────────────────
    if arm_model == "mobile_px100":
        p = "mobile_px100_meshes/mobile_px100"

        add(f"{p}_1_base.stl", tf_arm_base, vis_rpy=(0, 0, -PI / 2))

        tf_sh = tf_arm_base @ make_tf(xyz=(0, 0, 0.04293))  # waist
        add(
            f"{p}_2_shoulder.stl", tf_sh,
            vis_xyz=(0, 0, -0.0022), vis_rpy=(0, 0, PI / 2),
        )

        tf_ua = tf_sh @ make_tf(xyz=(0, 0, 0.04225))  # shoulder
        add(f"{p}_3_upper_arm.stl", tf_ua, vis_rpy=(0, 0, PI / 2))

        tf_fa = tf_ua @ make_tf(xyz=(0.035, 0, 0.1))  # elbow
        add(f"{p}_4_forearm.stl", tf_fa, vis_rpy=(0, 0, PI / 2))

        tf_gr = tf_fa @ make_tf(xyz=(0.1, 0, 0))  # wrist_angle
        add(f"{p}_5_gripper.stl", tf_gr, vis_rpy=(0, 0, PI / 2))

        tf_ee = tf_gr @ make_tf(xyz=(0.063, 0, 0))  # ee_arm (fixed)

        tf_gp = tf_ee @ make_tf(xyz=(0.0055, 0, 0))  # gripper
        add(
            f"{p}_6_gripper_prop.stl", tf_gp,
            vis_xyz=(-0.0685, 0, 0), vis_rpy=(0, 0, PI / 2),
        )

        tf_ar = tf_ee @ make_tf(xyz=(-0.017, 0, 0.04155))  # ar_tag
        add(f"{p}_9_ar_tag.stl", tf_ar)

        if show_gripper_bar:
            tf_gb = tf_ee @ make_tf(xyz=(0, 0, 0))
            add(
                f"{p}_7_gripper_bar.stl", tf_gb,
                vis_xyz=(-0.063, 0, 0), vis_rpy=(0, 0, PI / 2),
            )
            tf_fi = tf_gb @ make_tf(xyz=(0.023, 0, 0))  # ee_bar
            if show_gripper_fingers:
                add(  # left finger
                    f"{p}_8_gripper_finger.stl", tf_fi,
                    vis_xyz=(0, 0.005, 0), vis_rpy=(PI, PI, 0),
                )
                add(  # right finger
                    f"{p}_8_gripper_finger.stl", tf_fi,
                    vis_xyz=(0, -0.005, 0), vis_rpy=(0, PI, 0),
                )

    # ─── wx200 ────────────────────────────────────────────────────────────
    elif arm_model == "mobile_wx200":
        p = "mobile_wx200_meshes/mobile_wx200"

        add(
            f"{p}_1_base.stl", tf_arm_base,
            vis_xyz=(-0.095773, 0, -0.10565023),
            vis_rpy=(PI / 2, 0, PI / 2),
        )

        tf_sh = tf_arm_base @ make_tf(xyz=(0, 0, 0.066175))  # waist
        add(
            f"{p}_2_shoulder.stl", tf_sh,
            vis_xyz=(0, 0, -0.003), vis_rpy=(0, 0, PI / 2),
        )

        tf_ua = tf_sh @ make_tf(xyz=(0, 0, 0.03865))  # shoulder
        add(f"{p}_3_upper_arm.stl", tf_ua, vis_rpy=(0, 0, PI / 2))

        tf_fa = tf_ua @ make_tf(xyz=(0.05, 0, 0.2))  # elbow
        add(f"{p}_4_forearm.stl", tf_fa, vis_rpy=(0, 0, PI / 2))

        tf_wr = tf_fa @ make_tf(xyz=(0.2, 0, 0))  # wrist_angle
        add(f"{p}_5_wrist.stl", tf_wr, vis_rpy=(0, 0, PI / 2))

        tf_gr = tf_wr @ make_tf(xyz=(0.065, 0, 0))  # wrist_rotate
        add(
            f"{p}_6_gripper.stl", tf_gr,
            vis_xyz=(-0.02, 0, 0), vis_rpy=(0, 0, PI / 2),
        )

        tf_ee = tf_gr @ make_tf(xyz=(0.043, 0, 0))  # ee_arm

        tf_gp = tf_ee @ make_tf(xyz=(0.0055, 0, 0))  # gripper
        add(
            f"{p}_7_gripper_prop.stl", tf_gp,
            vis_xyz=(-0.0685, 0, 0), vis_rpy=(0, 0, PI / 2),
        )

        tf_ar = tf_ee @ make_tf(xyz=(-0.017, 0, 0.04155))
        add(f"{p}_10_ar_tag.stl", tf_ar)

        if show_gripper_bar:
            tf_gb = tf_ee @ make_tf(xyz=(0, 0, 0))
            add(
                f"{p}_8_gripper_bar.stl", tf_gb,
                vis_xyz=(-0.063, 0, 0), vis_rpy=(0, 0, PI / 2),
            )
            tf_fi = tf_gb @ make_tf(xyz=(0.023, 0, 0))
            if show_gripper_fingers:
                add(
                    f"{p}_9_gripper_finger.stl", tf_fi,
                    vis_xyz=(0, 0.005, 0), vis_rpy=(PI, PI, 0),
                )
                add(
                    f"{p}_9_gripper_finger.stl", tf_fi,
                    vis_xyz=(0, -0.005, 0), vis_rpy=(0, PI, 0),
                )

    # ─── wx250s ───────────────────────────────────────────────────────────
    elif arm_model == "mobile_wx250s":
        p = "mobile_wx250s_meshes/mobile_wx250s"

        add(
            f"{p}_1_base.stl", tf_arm_base,
            vis_xyz=(-0.095773, 0, -0.10565023),
            vis_rpy=(PI / 2, 0, PI / 2),
        )

        tf_sh = tf_arm_base @ make_tf(xyz=(0, 0, 0.066175))  # waist
        add(
            f"{p}_2_shoulder.stl", tf_sh,
            vis_xyz=(0, 0, -0.003), vis_rpy=(0, 0, PI / 2),
        )

        tf_ua = tf_sh @ make_tf(xyz=(0, 0, 0.03865))  # shoulder
        add(f"{p}_3_upper_arm.stl", tf_ua, vis_rpy=(0, 0, PI / 2))

        tf_uf = tf_ua @ make_tf(xyz=(0.04975, 0, 0.25))  # elbow
        add(f"{p}_4_upper_forearm.stl", tf_uf)

        tf_lf = tf_uf @ make_tf(xyz=(0.175, 0, 0))  # forearm_roll
        add(f"{p}_5_lower_forearm.stl", tf_lf, vis_rpy=(PI, 0, 0))

        tf_wr = tf_lf @ make_tf(xyz=(0.075, 0, 0))  # wrist_angle
        add(f"{p}_6_wrist.stl", tf_wr, vis_rpy=(0, 0, PI / 2))

        tf_gr = tf_wr @ make_tf(xyz=(0.065, 0, 0))  # wrist_rotate
        add(
            f"{p}_7_gripper.stl", tf_gr,
            vis_xyz=(-0.02, 0, 0), vis_rpy=(0, 0, PI / 2),
        )

        tf_ee = tf_gr @ make_tf(xyz=(0.043, 0, 0))  # ee_arm

        tf_gp = tf_ee @ make_tf(xyz=(0.0055, 0, 0))  # gripper
        add(
            f"{p}_8_gripper_prop.stl", tf_gp,
            vis_xyz=(-0.0685, 0, 0), vis_rpy=(0, 0, PI / 2),
        )

        tf_ar = tf_ee @ make_tf(xyz=(-0.017, 0, 0.04155))
        add(f"{p}_11_ar_tag.stl", tf_ar)

        if show_gripper_bar:
            tf_gb = tf_ee @ make_tf(xyz=(0, 0, 0))
            add(
                f"{p}_9_gripper_bar.stl", tf_gb,
                vis_xyz=(-0.063, 0, 0), vis_rpy=(0, 0, PI / 2),
            )
            tf_fi = tf_gb @ make_tf(xyz=(0.023, 0, 0))
            if show_gripper_fingers:
                add(
                    f"{p}_10_gripper_finger.stl", tf_fi,
                    vis_xyz=(0, 0.005, 0), vis_rpy=(PI, PI, 0),
                )
                add(
                    f"{p}_10_gripper_finger.stl", tf_fi,
                    vis_xyz=(0, -0.005, 0), vis_rpy=(0, PI, 0),
                )

    else:
        raise ValueError(f"Unknown arm_model {arm_model!r}.")

    return entries


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

# Hardcoded fallback used only when interbotix_black.png cannot be read.
_FALLBACK_COLOR = np.array([40, 40, 40, 255], dtype=np.uint8)


def _sample_png_color(png_path: Path) -> np.ndarray:
    """Return the mean RGBA colour of a PNG as a uint8 (4,) array.

    Requires Pillow.  Falls back to *_FALLBACK_COLOR* if the file cannot
    be read or Pillow is not installed.
    """
    try:
        from PIL import Image  # type: ignore
        arr = np.asarray(
            Image.open(png_path).convert("RGBA")
        ).reshape(-1, 4)
        return arr.mean(axis=0).round().astype(np.uint8)
    except ImportError:
        print(
            "  [note] Pillow not installed — using fallback colour instead"
            " of sampling interbotix_black.png.  Run: pip install Pillow"
        )
    except Exception as exc:
        print(f"  [warn] Could not sample {png_path.name}: {exc}")
    return _FALLBACK_COLOR.copy()


def _ensure_vertex_colors(
    mesh: trimesh.Trimesh,
    default_color: np.ndarray,
) -> None:
    """Assign vertex colours to *mesh* in-place.

    Strategy:
    - For DAE files loaded with pycollada, trimesh produces a
      TextureVisuals (UV texture) or ColorVisuals with per-material
      colours.  Calling ``to_color()`` samples the texture at each UV
      coordinate, giving genuine per-vertex colour variation — kept as-is.
    - STL files carry no colour or UV data.  trimesh assigns a uniform
      default grey, which ``to_color()`` returns as a constant array.
      Any uniform colour is treated as "no real data" and replaced with
      *default_color* (sampled from interbotix_black.png).
    """
    try:
        vc = mesh.visual.to_color().vertex_colors  # (N, 4) uint8
    except Exception:
        vc = None

    has_real_colors = (
        vc is not None
        and len(vc) > 0
        and not np.all(vc == vc[0])  # more than one unique colour
    )

    if has_real_colors:
        mesh.visual = trimesh.visual.color.ColorVisuals(
            mesh=mesh, vertex_colors=vc
        )
    else:
        mesh.visual = trimesh.visual.color.ColorVisuals(
            mesh=mesh,
            vertex_colors=np.tile(default_color, (len(mesh.vertices), 1)),
        )


# ---------------------------------------------------------------------------
# Mesh loading
# ---------------------------------------------------------------------------

def _load_one(
    path: Path,
    transform: np.ndarray,
    default_color: np.ndarray,
) -> Optional[trimesh.Trimesh]:
    """Load a mesh file, assign vertex colours, apply the world transform.

    STL files are forced to a single Trimesh.  DAE (Collada) files are
    loaded without ``force='mesh'`` so that pycollada can resolve
    material/texture references before we flatten the scene — this gives
    ``_ensure_vertex_colors`` access to the sampled texture colours rather
    than a blank visual.
    """
    is_dae = path.suffix.lower() == ".dae"
    try:
        if is_dae:
            # Preserve the Collada scene graph so textures are resolved.
            loaded = trimesh.load(str(path))
        else:
            loaded = trimesh.load(str(path), force="mesh")
    except Exception as exc:
        print(f"  [warn] Could not load {path.name}: {exc}")
        return None

    if isinstance(loaded, trimesh.Scene):
        # Flatten the scene; scene-graph transforms are baked in by dump().
        try:
            mesh = loaded.dump(concatenate=True)
        except Exception:
            geoms = list(loaded.geometry.values())
            if not geoms:
                print(f"  [warn] Empty scene in {path.name}, skipping.")
                return None
            mesh = trimesh.util.concatenate(geoms)
    elif isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
    else:
        print(
            f"  [warn] Unexpected type {type(loaded).__name__}"
            f" for {path.name}, skipping."
        )
        return None

    _ensure_vertex_colors(mesh, default_color)
    mesh.apply_transform(transform)
    return mesh


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble LoCoBot URDF meshes into a single .ply file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Kobuki base + PincherX-100 arm (default)
  python assemble_locobot_mesh.py

  # Create3 base + WidowX-200 arm, no lidar
  python assemble_locobot_mesh.py \\
      --base-model create3 --arm-model mobile_wx200 --no-lidar

  # Kobuki base only (no arm)
  python assemble_locobot_mesh.py \\
      --arm-model mobile_base --output locobot_base.ply
        """,
    )
    parser.add_argument(
        "--base-model", default="kobuki", choices=["kobuki", "create3"],
        help="Mobile base platform (default: kobuki)",
    )
    parser.add_argument(
        "--arm-model", default="mobile_px100",
        choices=[
            "mobile_px100", "mobile_wx200",
            "mobile_wx250s", "mobile_base",
        ],
        help="Arm model, or 'mobile_base' for no arm (default: mobile_px100)",
    )
    parser.add_argument(
        "--no-lidar", action="store_true",
        help="Exclude the LiDAR tower and sensor",
    )
    parser.add_argument(
        "--no-gripper-bar", action="store_true",
        help="Exclude the gripper bar (implies no fingers)",
    )
    parser.add_argument(
        "--no-gripper-fingers", action="store_true",
        help="Exclude the gripper fingers (bar kept unless --no-gripper-bar)",
    )
    parser.add_argument(
        "--output", default="locobot.ply",
        help="Output .ply file path (default: locobot.ply)",
    )
    parser.add_argument(
        "--meshes-dir",
        help=(
            "Path to the meshes/ directory inside"
            " interbotix_xslocobot_descriptions."
            " Auto-detected relative to this script if not given."
        ),
    )
    args = parser.parse_args()

    # ── Resolve meshes directory ──────────────────────────────────────────
    if args.meshes_dir:
        meshes_dir = Path(args.meshes_dir).resolve()
    else:
        script_dir = Path(__file__).resolve().parent
        meshes_dir = (
            script_dir
            / "interbotix_ros_xslocobots"
            / "interbotix_xslocobot_descriptions"
            / "meshes"
        )

    if not meshes_dir.is_dir():
        print(
            f"Error: meshes directory not found:\n  {meshes_dir}\n"
            "Use --meshes-dir to specify its location.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Resolve vertex colour from interbotix_black.png ───────────────────
    png_path = meshes_dir / "interbotix_black.png"
    if png_path.exists():
        robot_color = _sample_png_color(png_path)
        print(f"Texture colour (mean of interbotix_black.png): {robot_color}")
    else:
        robot_color = _FALLBACK_COLOR.copy()
        print(
            f"  [note] interbotix_black.png not found;"
            f" using fallback colour {robot_color}."
        )

    # ── Print summary ─────────────────────────────────────────────────────
    show_lidar = not args.no_lidar
    show_bar = not args.no_gripper_bar
    show_fingers = show_bar and not args.no_gripper_fingers

    print("Configuration")
    print(f"  base model : {args.base_model}")
    print(f"  arm model  : {args.arm_model}")
    print(f"  lidar      : {'yes' if show_lidar else 'no'}")
    print(f"  gripper bar: {'yes' if show_bar else 'no'}")
    print(f"  fingers    : {'yes' if show_fingers else 'no'}")
    print(f"  meshes dir : {meshes_dir}")
    print(f"  output     : {args.output}")
    print()

    # ── Build mesh list ───────────────────────────────────────────────────
    entries = _build_entries(
        base_model=args.base_model,
        arm_model=args.arm_model,
        show_lidar=show_lidar,
        show_gripper_bar=show_bar,
        show_gripper_fingers=show_fingers,
    )

    # ── Load and transform meshes ─────────────────────────────────────────
    print(f"Loading {len(entries)} mesh entries...")
    meshes: List[trimesh.Trimesh] = []

    for rel_path, link_tf, vis_xyz, vis_rpy, scale in entries:
        full_path = meshes_dir / rel_path
        if not full_path.exists():
            print(f"  [skip] not found: {rel_path}")
            continue

        # Final transform = T_link_world @ T_visual_origin @ S_scale
        final_tf = (
            link_tf
            @ make_tf(vis_xyz, vis_rpy)
            @ np.diag([scale, scale, scale, 1.0])
        )

        print(f"  loading : {full_path.name}")
        mesh = _load_one(full_path, final_tf, robot_color)
        if mesh is not None:
            meshes.append(mesh)

    if not meshes:
        print("Error: no meshes could be loaded.", file=sys.stderr)
        sys.exit(1)

    # ── Merge and export ──────────────────────────────────────────────────
    print(f"\nMerging {len(meshes)} mesh(es)...")
    merged = trimesh.util.concatenate(meshes)
    print(f"  vertices : {len(merged.vertices):,}")
    print(f"  faces    : {len(merged.faces):,}")

    out_path = Path(args.output)
    ply_bytes = trimesh.exchange.ply.export_ply(merged, encoding="ascii")
    out_path.write_bytes(ply_bytes)
    print(f"\nSaved -> {out_path.resolve()}")


if __name__ == "__main__":
    main()
