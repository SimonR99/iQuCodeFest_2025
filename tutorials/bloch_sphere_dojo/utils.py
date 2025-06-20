import numpy as np
import plotly.graph_objs as go
from numpy import pi, sin, cos
import numpy as np
import plotly.graph_objs as go
from typing import List, Tuple, Optional
from dataclasses import dataclass
import re

import numpy as np
from typing import List, Optional, Union
from dataclasses import dataclass
import plotly.graph_objects as go




@dataclass
class Point3D:
    """Represents a point on the Bloch sphere"""
    x: float
    y: float
    z: float

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Point3D':
        return cls(float(arr[0]), float(arr[1]), float(arr[2]))


QUANTUM_STATES = {
    "+": [1/np.sqrt(2), 1/np.sqrt(2)],
    "-": [1/np.sqrt(2), -1/np.sqrt(2)],
    "+i": [1/np.sqrt(2), 1/np.sqrt(2)*1j],
    "-i": [1/np.sqrt(2), -1/np.sqrt(2)*1j],
    "0": [1, 0],
    "1": [0, 1]
}

QUANTUM_STATES_Point3D = {
    "+": Point3D(1,0,0), # x, y, z
    "-": Point3D(-1,0,0),
    "+i": Point3D(0,1,0),
    "-i": Point3D(0,-1,0),
    "0": Point3D(0,0,1),
    "1": Point3D(0,0,-1)
}


class BlochRotation:
    @staticmethod
    def rotate_points(axis: str, start_point: Point3D, angle: float = None, num_steps: int = 20) -> List[Point3D]:
        """
        Rotate a point around specified axis
        num_steps : Number of intermediate points for smooth rotation
        """
        points = []
        if axis in ['X', 'Z']:
            for step in range(num_steps + 1):
                t = step / num_steps
                current_angle = angle * t
                if axis == 'X':
                    new_point = BlochRotation._rotate_x(start_point, current_angle)
                else:  # Z rotation
                    new_point = BlochRotation._rotate_z(start_point, current_angle)
                points.append(new_point)
        elif axis == 'H':
            # Hadamard gate is equivalent to a rotation by π around the axis n = (1,0,1)/√2
            nx = 1 / np.sqrt(2)
            ny = 0
            nz = 1 / np.sqrt(2)
            angle = np.pi  # Hadamard is a π rotation

            for step in range(num_steps + 1):
                t = step / num_steps
                current_angle = angle * t

                # Rotation matrix around arbitrary axis
                c = np.cos(current_angle)
                s = np.sin(current_angle)
                v = 1 - c

                # Rotation matrix elements
                R11 = nx * nx * v + c
                R12 = nx * ny * v - nz * s
                R13 = nx * nz * v + ny * s
                R21 = ny * nx * v + nz * s
                R22 = ny * ny * v + c
                R23 = ny * nz * v - nx * s
                R31 = nz * nx * v - ny * s
                R32 = nz * ny * v + nx * s
                R33 = nz * nz * v + c

                # Apply rotation
                x = start_point.x * R11 + start_point.y * R12 + start_point.z * R13
                y = start_point.x * R21 + start_point.y * R22 + start_point.z * R23
                z = start_point.x * R31 + start_point.y * R32 + start_point.z * R33

                points.append(Point3D(x, y, z))
        else:
            raise ValueError(f"Unknown rotation axis: {axis}")

        return points

    @staticmethod
    def _rotate_x(point: Point3D, angle: float) -> Point3D:
        """Rotate around X axis"""
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        return Point3D(
            point.x,
            point.y * cos_a - point.z * sin_a,
            point.y * sin_a + point.z * cos_a
        )

    @staticmethod
    def _rotate_y(point: Point3D, angle: float) -> Point3D:
        """Rotate around Y axis"""
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        return Point3D(
            point.x * cos_a + point.z * sin_a,
            point.y,
            -point.x * sin_a + point.z * cos_a
        )

    @staticmethod
    def _rotate_z(point: Point3D, angle: float) -> Point3D:
        """Rotate around Z axis"""
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        return Point3D(
            point.x * cos_a - point.y * sin_a,
            point.x * sin_a + point.y * cos_a,
            point.z
        )


# Define a class to manage operations
@dataclass
class BlochOperation:
    axis: str
    angle: float
    color: str


class BlochGate:
    @staticmethod
    def X_gate(color: str = 'red') -> BlochOperation:
        return BlochOperation(axis='X', angle=np.pi, color=color)

    @staticmethod
    def Z_gate(color: str = 'blue') -> BlochOperation:
        return BlochOperation(axis='Z', angle=np.pi, color=color)

    @staticmethod
    def T_gate(color: str = 'purple') -> BlochOperation:
        return BlochOperation(axis='Z', angle=np.pi / 2, color=color)

    @staticmethod
    def T_dag_gate(color: str = 'orange') -> BlochOperation:
        return BlochOperation(axis='Z', angle=-np.pi / 2, color=color)

    @staticmethod
    def S_gate(color: str = 'cyan') -> BlochOperation:
        return BlochOperation(axis='Z', angle=np.pi / 4, color=color)

    @staticmethod
    def S_dag_gate(color: str = 'magenta') -> BlochOperation:
        return BlochOperation(axis='Z', angle=-np.pi / 4, color=color)

    @staticmethod
    def Rx(angle: float, color: str = 'red') -> BlochOperation:
        return BlochOperation(axis='X', angle=angle, color=color)

    @staticmethod
    def Rz(angle: float, color: str = 'blue') -> BlochOperation:
        return BlochOperation(axis='Z', angle=angle, color=color)

    @staticmethod
    def H_gate(color: str = 'yellow') -> BlochOperation:
        return BlochOperation(axis='H', angle=np.pi, color=color)


def generate_trajectory(initial_point: Point3D, operations: List[BlochOperation]) -> Tuple[List[Point3D], List[str]]:
    """
    Generate trajectory on the Bloch sphere based on the given operations.
    """
    trajectory_points = [initial_point]
    colors = []
    current_point = initial_point

    for op in operations:
        segment_points = BlochRotation.rotate_points(op.axis, current_point, op.angle)
        trajectory_points.extend(segment_points[1:])  # Avoid duplicating the starting point
        colors.extend([op.color] * len(segment_points[1:]))
        current_point = segment_points[-1]

    return trajectory_points, colors


def generate_optimized_trajectory(start_point: Point3D, operations: List[BlochOperation], num_intermediate_points=5):
    """Generates an optimized trajectory on the Bloch sphere given a starting point and a list of operations."""
    trajectory_points = [start_point]
    colors = []
    current_point = start_point

    for op in operations:
        intermediate_points = BlochRotation.rotate_points(axis=op.axis, start_point=current_point, angle=op.angle, num_steps=num_intermediate_points)
        trajectory_points.extend(intermediate_points[1:])  # Avoid duplicating the current_point
        current_point = intermediate_points[-1]
        # Alternate between two colors for visualization (e.g., blue and red)
        ## colors.extend(['blue', 'red'] * (num_intermediate_points // 2)) # have pbm
        colors.extend([op.color] * len(intermediate_points[1:]))

    return trajectory_points, colors

class BlochSphereVisualizer:
    """Enhanced Bloch sphere visualization with efficient caching and flexible rendering options"""

    def __init__(self):
        # Cache mesh data to avoid recalculation
        self._mesh_data = None
        self._base_figure = None
        self.camera_eye_x_right = {
                "x": 1.3439309286879517,
                "y": -0.45171390093395863,
                "z": 1.1545707086648742
            }
        
        self.camera_eye_default = {"x": 1.5, "y": 1.5, "z": 1}


    def _create_sphere_mesh(self, phi_points: int = 20, theta_points: int = 40) -> Tuple[
    List[float], List[float], List[float]]:
        """
        Create Bloch sphere wireframe with configurable resolution.

        Args:
            phi_points: Number of points for phi angle discretization
            theta_points: Number of points for theta angle discretization

        Returns:
            Tuple containing lists of x, y, z coordinates for the sphere mesh
        """
        if self._mesh_data is not None:
            return self._mesh_data

        phi = np.linspace(0, np.pi, phi_points)
        theta = np.linspace(0, 2 * np.pi, theta_points)

        x, y, z = [], [], []

        # Create meridians
        for t in theta:
            x.extend([np.sin(p) * np.cos(t) for p in phi] + [None])
            y.extend([np.sin(p) * np.sin(t) for p in phi] + [None])
            z.extend([np.cos(p) for p in phi] + [None])

        # Create parallels
        for p in phi[1:-1]:
            x.extend([np.sin(p) * np.cos(t) for t in theta] + [None])
            y.extend([np.sin(p) * np.sin(t) for t in theta] + [None])
            z.extend([np.cos(p)] * (len(theta) + 1))

        self._mesh_data = (x, y, z)
        return self._mesh_data


    def _get_base_figure(self) -> go.Figure:
        """Create or retrieve cached base figure with sphere and axes"""
        if self._base_figure is not None:
            return go.Figure(self._base_figure)

        fig = go.Figure()

        # Add Bloch sphere
        x_sphere, y_sphere, z_sphere = self._create_sphere_mesh()
        fig.add_trace(go.Scatter3d(
            x=x_sphere, y=y_sphere, z=z_sphere,
            mode='lines',
            line=dict(color='gray', width=1),
            opacity=0.3,
            name='Bloch Sphere'
        ))

        # Add axes with labels
        axes = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        labels = ['x', 'z']
        colors = ['red', 'green', 'blue']

        for axis, label, color in zip(axes, labels, colors):
            fig.add_trace(go.Scatter3d(
                x=[0, axis[0]], y=[0, axis[1]], z=[0, axis[2]],
                mode='lines',
                line=dict(color=color, width=3),
                name=f'{label}-axis'
            ))

        # Configure layout
        fig.update_layout(
            scene=dict(
                aspectmode='cube',
                xaxis_title='X',
                zaxis_title='Z'
            ),
            showlegend=True
        )

        self._base_figure = fig
        return go.Figure(fig)


    @staticmethod
    def _get_default_scene_settings(camera_eye: Optional[dict] = {"x": 1.5, "y": 1.5, "z": 1},
                                   axis_range: float = 1.2) -> dict:
        """
        Construct the 3D scene settings for the Bloch sphere.

        Args:
            camera_eye: Dictionary containing the x, y, z coordinates of the camera
            axis_range: The range for the x, y, and z axes

        Returns:
            Dictionary containing scene settings for plotly
        """
    
        return dict(
            aspectmode='cube',
            camera=dict(
                eye=camera_eye,
                center=dict(x=0, y=0, z=0),
                up=dict(x=0, y=0, z=1)
            ),
            xaxis=dict(range=[-axis_range, axis_range]),
            yaxis=dict(range=[-axis_range, axis_range]),
            zaxis=dict(range=[-axis_range, axis_range])
        )


    def _process_operations_or_trajectory(self, input_data: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                        initial_point: Point3D) -> Tuple[List[Point3D], List[str]]:
        """
        Process the input data to generate or unpack trajectory points and colors.
        
        Args:
            input_data: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]] - List of operations or precomputed trajectory
            initial_point: Point3D - The starting point for the trajectory
        
        Returns:
            Tuple[List[Point3D], List[str]] - Trajectory points and trajectory colors
        """
        if isinstance(input_data, list) and all(isinstance(op, BlochOperation) for op in input_data):
            points, colors = generate_trajectory(initial_point, input_data)
        else:
            points, colors = input_data

        return points, colors


    def _create_animation_layout(self, camera_eye, frames: List[go.Frame], frame_duration: int) -> go.Layout:
        """Create standard animation layout with controls"""
        go_fig_layout = go.Layout(
            scene=self._get_default_scene_settings(camera_eye),
            updatemenus=[{
                "buttons": [
                    {
                        "args": [None, {"frame": {"duration": frame_duration},
                                        "fromcurrent": True,
                                        "transition": {"duration": 0}}],
                        "label": "Play",
                        "method": "animate"
                    },
                    {
                        "args": [[None], {"frame": {"duration": 0},
                                          "mode": "immediate",
                                          "transition": {"duration": 0}}],
                        "label": "Pause",
                        "method": "animate"
                    }
                ],
                "type": "buttons"
            }],
            sliders=[{
                "currentvalue": {"prefix": "Frame: "},
                "steps": [
                    {
                        "args": [[f.name], {"frame": {"duration": 0},
                                            "mode": "immediate",
                                            "transition": {"duration": 0}}],
                        "label": str(k),
                        "method": "animate"
                    }
                    for k, f in enumerate(frames)
                ]
            }]
        )

        return go_fig_layout



    def plot_trajectory(self,
                        trajectory_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                        initial_point:Point3D = Point3D(0,0,1),
                        line_color: str = 'black',
                        line_width: int = 4,
                        marker_size: int = 4) -> go.Figure:
        """
        Create a static 3D plot for a single trajectory.

        Args:
            trajectory_points: List of points in the trajectory
            trajectory_colors: List of colors for each point
            line_color: Color of the connecting line
            line_width: Width of the connecting line
            marker_size: Size of the point markers

        Returns:
            Plotly figure object
        """
        fig = self._get_base_figure()

        # Process input data to generate or unpack trajectories
        trajectory_points, trajectory_colors = self._process_operations_or_trajectory(trajectory_ops, initial_point)


        x = [p.x for p in trajectory_points]
        y = [p.y for p in trajectory_points]
        z = [p.z for p in trajectory_points]

        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines+markers',
            line=dict(color=line_color, width=line_width),
            marker=dict(size=marker_size, color=trajectory_colors),
            name='Trajectory'
        ))

        return fig


    def animate_trajectory(self, trajectory_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                           initial_point: Point3D = Point3D(0, 0, 1), frame_duration: int = 100,
                           line_color: str = 'black', line_width: int = 4, marker_size: int = 4,
                           is_camera_eye_x_right: bool =True) -> go.Figure:
        """
        Create an animated visualization of a trajectory.

        Args:
            trajectory_points: List of points in the trajectory
            trajectory_colors: List of colors for each point
            frame_duration: Duration of each animation frame
            line_color: Color of the connecting line
            line_width: Width of the connecting line
            marker_size: Size of the point markers

        Returns:
            Plotly figure object with animation
            :param is_camera_left:
        """
        base_figure = self._get_base_figure()

        # Process input data to generate or unpack trajectories
        trajectory_points, trajectory_colors = self._process_operations_or_trajectory(trajectory_ops, initial_point)


        frames = []

        for i in range(len(trajectory_points)):
            frame_data = list(base_figure.data) + [
                go.Scatter3d(
                    x=[p.x for p in trajectory_points[:i + 1]],
                    y=[p.y for p in trajectory_points[:i + 1]],
                    z=[p.z for p in trajectory_points[:i + 1]],
                    mode='lines+markers',
                    line=dict(color=line_color, width=line_width),
                    marker=dict(size=marker_size, color=trajectory_colors[:i + 1]),
                    name='Trajectory'
                )
            ]
            frames.append(go.Frame(data=frame_data, name=f'frame{i}'))

        if is_camera_eye_x_right:
            camera_eye = self.camera_eye_x_right
        else:
            camera_eye = self.camera_eye_default

        fig = go.Figure(
            data=frames[0].data,
            frames=frames,
            layout=self._create_animation_layout(camera_eye=camera_eye,
                                                 frames=frames, 
                                                 frame_duration=frame_duration)
        )

        return fig
    

    def plot_dual_trajectories_static(self,
                                           exercise_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           student_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           initial_point: Point3D = Point3D(0, 0, 1)) -> go.Figure:
        """Create animation showing both trajectories evolving simultaneously"""
        
        fig = self._get_base_figure()

        # Process input data to generate or unpack trajectories
        exercise_points, exercise_colors = self._process_operations_or_trajectory(exercise_ops, initial_point)
        student_points, student_colors = self._process_operations_or_trajectory(student_ops, initial_point)


        x_exercise = [p.x for p in exercise_points]
        y_exercise = [p.y for p in exercise_points]
        z_exercise = [p.z for p in exercise_points]

        x_student = [p.x for p in student_points]
        y_student = [p.y for p in student_points]
        z_student = [p.z for p in student_points]

        # Add exercise trajectory
        fig.add_trace(go.Scatter3d(
            x=x_exercise, y=y_exercise, z=z_exercise,
            mode='lines',
            line=dict(color='blue', width=4),
            name='Exercise Path'
        ))

        # Add student trajectory
        fig.add_trace(go.Scatter3d(
            x=x_student, y=y_student, z=z_student,
            mode='lines',
            line=dict(color='red', width=4),
            name='Your Path'
        ))

        return fig

    def animate_dual_trajectories_simultaneous(self,
                                           exercise_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           student_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           initial_point: Point3D = Point3D(0, 0, 1),
                                           frame_duration: int = 100) -> go.Figure:
        """Create animation showing both trajectories evolving simultaneously"""
        base_figure = self._get_base_figure()

        # Process input data to generate or unpack trajectories
        exercise_points, exercise_colors = self._process_operations_or_trajectory(exercise_ops, initial_point)
        student_points, student_colors = self._process_operations_or_trajectory(student_ops, initial_point)


        # Create frames
        frames = []
        max_points = max(len(exercise_points), len(student_points))

        for i in range(max_points):
            # Get current points for both trajectories
            ex_idx = min(i, len(exercise_points) - 1)
            st_idx = min(i, len(student_points) - 1)

            frame_data = list(base_figure.data) + [
                # Exercise trajectory
                go.Scatter3d(
                    x=[p.x for p in exercise_points[:ex_idx + 1]],
                    y=[p.y for p in exercise_points[:ex_idx + 1]],
                    z=[p.z for p in exercise_points[:ex_idx + 1]],
                    mode='lines+markers',
                    line=dict(color='blue', width=4),
                    marker=dict(size=4, color=exercise_colors[:ex_idx + 1]),
                    name='Exercise Path'
                ),
                # Student trajectory
                go.Scatter3d(
                    x=[p.x for p in student_points[:st_idx + 1]],
                    y=[p.y for p in student_points[:st_idx + 1]],
                    z=[p.z for p in student_points[:st_idx + 1]],
                    mode='lines+markers',
                    line=dict(color='red', width=4),
                    marker=dict(size=4, color=student_colors[:st_idx + 1]),
                    name='Your Path'
                )
            ]
            frames.append(go.Frame(data=frame_data, name=f'frame{i}'))

        # Create figure with animation controls
        fig = go.Figure(
            data=frames[0].data,
            frames=frames,
            layout=self._create_animation_layout(self.camera_eye_default, frames, frame_duration)
        )

        return fig


    def animate_dual_trajectories_sequential(self, 
                                           exercise_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           student_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           initial_point: Point3D = Point3D(0, 0, 1),
                                            frame_duration: int = 100) -> go.Figure:
        """Create animation showing exercise trajectory followed by student trajectory"""
        base_figure = self._get_base_figure()

        # Process input data to generate or unpack trajectories
        exercise_points, exercise_colors = self._process_operations_or_trajectory(exercise_ops, initial_point)
        student_points, student_colors = self._process_operations_or_trajectory(student_ops, initial_point)

        # Initialize with empty trajectories but proper traces
        fig = go.Figure(base_figure)
        
        # Add initial empty traces for both paths
        fig.add_trace(
            go.Scatter3d(
                x=[initial_point.x], 
                y=[initial_point.y], 
                z=[initial_point.z],
                mode='markers',
                marker=dict(size=6, color='blue'),
                name='Exercise Path'
            )
        )
        
        fig.add_trace(
            go.Scatter3d(
                x=[initial_point.x], 
                y=[initial_point.y], 
                z=[initial_point.z],
                mode='markers',
                marker=dict(size=6, color='red'),
                name='Your Path'
            )
        )

        frames = []
        
        # First animate exercise trajectory
        for i in range(len(exercise_points)):
            frame_data = list(base_figure.data)  # Start with base sphere and axes
            frame_data.append(
                go.Scatter3d(
                    x=[p.x for p in exercise_points[:i + 1]],
                    y=[p.y for p in exercise_points[:i + 1]],
                    z=[p.z for p in exercise_points[:i + 1]],
                    mode='lines+markers',
                    line=dict(color='blue', width=4),
                    marker=dict(size=4, color=exercise_colors[:i + 1]),
                    name='Exercise Path'
                )
            )
            # Add static point for student path
            frame_data.append(
                go.Scatter3d(
                    x=[initial_point.x],
                    y=[initial_point.y],
                    z=[initial_point.z],
                    mode='markers',
                    marker=dict(size=6, color='red'),
                    name='Your Path'
                )
            )
            frames.append(go.Frame(data=frame_data, name=f'frame{i}'))

        # Then animate student trajectory
        for i in range(len(student_points)):
            frame_idx = i + len(exercise_points)
            frame_data = list(base_figure.data)
            
            # Add complete exercise trajectory
            frame_data.append(
                go.Scatter3d(
                    x=[p.x for p in exercise_points],
                    y=[p.y for p in exercise_points],
                    z=[p.z for p in exercise_points],
                    mode='lines+markers',
                    line=dict(color='blue', width=4),
                    marker=dict(size=4, color=exercise_colors[:i + 1]),
                    name='Exercise Path'
                )
            )
            
            # Add growing student trajectory
            frame_data.append(
                go.Scatter3d(
                    x=[p.x for p in student_points[:i + 1]],
                    y=[p.y for p in student_points[:i + 1]],
                    z=[p.z for p in student_points[:i + 1]],
                    mode='lines+markers',
                    line=dict(color='red', width=4),
                    marker=dict(size=4, color=student_colors[:i + 1]),
                    name='Your Path'
                )
            )
            frames.append(go.Frame(data=frame_data, name=f'frame{frame_idx}'))

        # Update layout
        fig.update_layout(
            scene=dict(
                aspectmode='cube',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1)),
                xaxis=dict(range=[-1.5, 1.5]),
                yaxis=dict(range=[-1.5, 1.5]),
                zaxis=dict(range=[-1.5, 1.5])
            ),
            updatemenus=[{
                "buttons": [
                    {
                        "args": [None, {"frame": {"duration": frame_duration},
                                    "fromcurrent": True,
                                    "mode": "immediate"}],
                        "label": "Play",
                        "method": "animate"
                    },
                    {
                        "args": [[None], {"frame": {"duration": 0},
                                        "mode": "immediate"}],
                        "label": "Pause",
                        "method": "animate"
                    }
                ],
                "type": "buttons",
                "showactive": False,
            }],
            sliders=[{
                "currentvalue": {"prefix": "Frame: "},
                "steps": [
                    {
                        "args": [[f.name], {"frame": {"duration": 0},
                                        "mode": "immediate"}],
                        "label": str(i),
                        "method": "animate"
                    }
                    for i, f in enumerate(frames)
                ]
            }]
        )
        
        # Add frames to figure
        fig.frames = frames

        return fig

    def animate_dual_trajectories_sequential_cam_l(self, 
                                           exercise_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           student_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
                                           initial_point: Point3D = Point3D(0, 0, 1),
                                            frame_duration: int = 100) -> go.Figure:
        """Create animation showing exercise trajectory followed by student trajectory"""
        base_figure = self._get_base_figure()

        # Process input data to generate or unpack trajectories
        exercise_points, exercise_colors = self._process_operations_or_trajectory(exercise_ops, initial_point)
        student_points, student_colors = self._process_operations_or_trajectory(student_ops, initial_point)


        # Initialize with empty trajectories but proper traces
        fig = go.Figure(base_figure)
        
        # Add initial empty traces for both paths
        fig.add_trace(
            go.Scatter3d(
                x=[initial_point.x], 
                y=[initial_point.y], 
                z=[initial_point.z],
                mode='markers',
                marker=dict(size=8, color='blue'),  # Increased marker size
                name='Exercise Path'
            )
        )
        
        fig.add_trace(
            go.Scatter3d(
                x=[initial_point.x], 
                y=[initial_point.y], 
                z=[initial_point.z],
                mode='markers',
                marker=dict(size=8, color='red'),  # Increased marker size
                name='Your Path'
            )
        )

        frames = []
        
        # First animate exercise trajectory
        for i in range(len(exercise_points)):
            frame_data = list(base_figure.data)  # Start with base sphere and axes
            frame_data.append(
                go.Scatter3d(
                    x=[p.x for p in exercise_points[:i + 1]],
                    y=[p.y for p in exercise_points[:i + 1]],
                    z=[p.z for p in exercise_points[:i + 1]],
                    mode='lines+markers',
                    line=dict(color='blue', width=5),  # Increased line width
                    marker=dict(size=6, color='blue'),  # Increased marker size
                    name='Exercise Path'
                )
            )
            # Add static point for student path
            frame_data.append(
                go.Scatter3d(
                    x=[initial_point.x],
                    y=[initial_point.y],
                    z=[initial_point.z],
                    mode='markers',
                    marker=dict(size=8, color='red'),  # Increased marker size
                    name='Your Path'
                )
            )
            frames.append(go.Frame(data=frame_data, name=f'frame{i}'))

        # Then animate student trajectory
        for i in range(len(student_points)):
            frame_idx = i + len(exercise_points)
            frame_data = list(base_figure.data)
            
            # Add complete exercise trajectory
            frame_data.append(
                go.Scatter3d(
                    x=[p.x for p in exercise_points],
                    y=[p.y for p in exercise_points],
                    z=[p.z for p in exercise_points],
                    mode='lines+markers',
                    line=dict(color='blue', width=5),  # Increased line width
                    marker=dict(size=6, color='blue'),  # Increased marker size
                    name='Exercise Path'
                )
            )
            
            # Add growing student trajectory
            frame_data.append(
                go.Scatter3d(
                    x=[p.x for p in student_points[:i + 1]],
                    y=[p.y for p in student_points[:i + 1]],
                    z=[p.z for p in student_points[:i + 1]],
                    mode='lines+markers',
                    line=dict(color='red', width=5),  # Increased line width
                    marker=dict(size=6, color='red'),  # Increased marker size
                    name='Your Path'
                )
            )
            frames.append(go.Frame(data=frame_data, name=f'frame{frame_idx}'))

        # Update layout with larger sphere and adjusted camera
        fig.update_layout(
            scene=dict(
                aspectmode='cube',
                camera=dict(
                    eye=dict(x=1.5, y=0.7, z=0.8),  # Moved camera closer
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1)
                ),
                xaxis=dict(range=[-1.2, 1.2]),  # Tightened axis ranges
                yaxis=dict(range=[-1.2, 1.2]),
                zaxis=dict(range=[-1.2, 1.2])
            ),
            updatemenus=[{
                "buttons": [
                    {
                        "args": [None, {"frame": {"duration": frame_duration},
                                    "fromcurrent": True,
                                    "mode": "immediate"}],
                        "label": "Play",
                        "method": "animate"
                    },
                    {
                        "args": [[None], {"frame": {"duration": 0},
                                        "mode": "immediate"}],
                        "label": "Pause",
                        "method": "animate"
                    }
                ],
                "type": "buttons",
                "showactive": False,
            }],
            sliders=[{
                "currentvalue": {"prefix": "Frame: "},
                "steps": [
                    {
                        "args": [[f.name], {"frame": {"duration": 0},
                                        "mode": "immediate"}],
                        "label": str(i),
                        "method": "animate"
                    }
                    for i, f in enumerate(frames)
                ]
            }]
        )
        
        # Add frames to figure
        fig.frames = frames

        return fig



class PointsBlochSphereVisualizer(BlochSphereVisualizer):
    """Enhanced Bloch sphere visualization with support for specific points and trajectories"""
    
    def plot_points_and_trajectory(self,
                                 depart: Point3D,
                                 arrivee: Point3D,
                                 intermediaire: Optional[Point3D] = None,
                                 trajectory_points: List[Point3D] = None,
                                 point_size: int = 8,
                                 trajectory_width: int = 4) -> go.Figure:
        """
        Create a Bloch sphere visualization with specific points and a trajectory.
        Intermediate point is optional.
        """
        # Get base figure with Bloch sphere
        fig = self._get_base_figure()
        
        # Add specific points with different colors and labels (only in legend)
        points_data = [
            (depart, 'red', 'Depart'),
            (arrivee, 'green', 'Arrivée')
        ]
        
        # Add intermediate point only if it exists
        if intermediaire is not None:
            points_data.append((intermediaire, 'blue', 'Intermédiaire'))
        
        for point, color, label in points_data:
            fig.add_trace(go.Scatter3d(
                x=[point.x],
                y=[point.y],
                z=[point.z],
                mode='markers',
                marker=dict(
                    size=point_size,
                    color=color,
                ),
                name=label,
                showlegend=True
            ))
        
        # Add trajectory if provided
        if trajectory_points:
            x_traj = [p.x for p in trajectory_points]
            y_traj = [p.y for p in trajectory_points]
            z_traj = [p.z for p in trajectory_points]
            
            fig.add_trace(go.Scatter3d(
                x=x_traj,
                y=y_traj,
                z=z_traj,
                mode='lines',
                line=dict(
                    color='purple',
                    width=trajectory_width
                ),
                name='Trajectory'
            ))
        
        # Update layout for better visualization
        fig.update_layout(
            scene=self._get_default_scene_settings(self.camera_eye_x_right),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='rgba(0, 0, 0, 0.2)',
                borderwidth=1,
                font=dict(size=10)  # Smaller legend font
            ),
            margin=dict(l=0, r=0, t=30, b=0),  # Reduced top margin
            height=700  # Increased figure height
        )
        
        return fig

    def animate_trajectory_with_points(self,
                                     depart: Point3D,
                                     arrivee: Point3D,
                                     intermediaire: Optional[Point3D] = None,
                                     trajectory_points: List[Point3D] = None,
                                     frame_duration: int = 100) -> go.Figure:
        """
        Create an animated visualization showing the trajectory evolution with fixed points.
        Intermediate point is optional.
        """
        base_figure = self._get_base_figure()
        frames = []
        
        # Add fixed points to each frame
        points_data = [
            (depart, 'red', 'Depart'),
            (arrivee, 'green', 'Arrivée')
        ]
        
        # Add intermediate point only if it exists
        if intermediaire is not None:
            points_data.append((intermediaire, 'blue', 'Intermédiaire'))
        
        if trajectory_points:
            for i in range(len(trajectory_points)):
                frame_data = list(base_figure.data)
                
                # Add fixed points
                for point, color, label in points_data:
                    frame_data.append(go.Scatter3d(
                        x=[point.x],
                        y=[point.y],
                        z=[point.z],
                        mode='markers',
                        marker=dict(size=8, color=color),
                        name=label
                    ))
                
                # Add growing trajectory
                frame_data.append(go.Scatter3d(
                    x=[p.x for p in trajectory_points[:i + 1]],
                    y=[p.y for p in trajectory_points[:i + 1]],
                    z=[p.z for p in trajectory_points[:i + 1]],
                    mode='lines',
                    line=dict(color='purple', width=4),
                    name='Trajectory'
                ))
                
                frames.append(go.Frame(data=frame_data, name=f'frame{i}'))
        
        # Create figure with animation controls
        fig = go.Figure(
            data=frames[0].data if frames else base_figure.data,
            frames=frames,
            layout=go.Layout(
                scene=self._get_default_scene_settings(self.camera_eye_x_right),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99,
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='rgba(0, 0, 0, 0.2)',
                    borderwidth=1,
                    font=dict(size=10)  # Smaller legend font
                ),
                updatemenus=[{
                    "buttons": [
                        {
                            "args": [None, {"frame": {"duration": frame_duration},
                                          "fromcurrent": True,
                                          "transition": {"duration": 0}}],
                            "label": "Play",
                            "method": "animate"
                        },
                        {
                            "args": [[None], {"frame": {"duration": 0},
                                            "mode": "immediate",
                                            "transition": {"duration": 0}}],
                            "label": "Pause",
                            "method": "animate"
                        }
                    ],
                    "type": "buttons",
                    "x": 0.1,  # Moved buttons to the left
                    "y": 0,    # Moved buttons to the bottom
                    "xanchor": "right",
                    "yanchor": "bottom"
                }],
                sliders=[{
                    "currentvalue": {"prefix": "Frame: ", "font": {"size": 10}},  # Smaller font
                    "len": 0.3,  # Shorter slider
                    "x": 0.15,   # Moved slider to the left
                    "y": 0,      # Moved slider to the bottom
                    "xanchor": "left",
                    "yanchor": "bottom",
                    "steps": [
                        {
                            "args": [[f"frame{k}"], {"frame": {"duration": 0},
                                                   "mode": "immediate",
                                                   "transition": {"duration": 0}}],
                            "label": str(k),
                            "method": "animate"
                        }
                        for k in range(len(frames))
                    ]
                }],
                margin=dict(l=0, r=0, t=30, b=30),  # Reduced top and bottom margins
                height=700  # Increased figure height
            )
        )
        
        return fig

    def plot_points_and_dual_trajectories(self,
                                        depart: Point3D,
                                        arrivee: Point3D,
                                        intermediaire: Optional[Point3D] = None,
                                        exercise_trajectory: List[Point3D] = None,
                                        student_trajectory: List[Point3D] = None,
                                        point_size: int = 8,
                                        trajectory_width: int = 4) -> go.Figure:
        """
        Create a Bloch sphere visualization with specific points and two trajectories.
        
        Args:
            depart: Starting point
            arrivee: End point
            intermediaire: Optional intermediate point
            exercise_trajectory: List of points for exercise trajectory
            student_trajectory: List of points for student trajectory
            point_size: Size of points markers
            trajectory_width: Width of trajectory lines
        """
        # Get base figure with Bloch sphere
        fig = self._get_base_figure()
        
        # Add specific points with different colors and labels
        points_data = [
            (depart, 'red', 'Depart'),
            (arrivee, 'green', 'Arrivée')
        ]
        
        if intermediaire is not None:
            points_data.append((intermediaire, 'blue', 'Intermédiaire'))
        
        for point, color, label in points_data:
            fig.add_trace(go.Scatter3d(
                x=[point.x],
                y=[point.y],
                z=[point.z],
                mode='markers',
                marker=dict(
                    size=point_size,
                    color=color,
                ),
                name=label,
                showlegend=True
            ))
        
        # Add exercise trajectory if provided
        if exercise_trajectory:
            x_traj = [p.x for p in exercise_trajectory]
            y_traj = [p.y for p in exercise_trajectory]
            z_traj = [p.z for p in exercise_trajectory]
            
            fig.add_trace(go.Scatter3d(
                x=x_traj,
                y=y_traj,
                z=z_traj,
                mode='lines',
                line=dict(
                    color='purple',
                    width=trajectory_width
                ),
                name='Exercise Path'
            ))
        
        # Add student trajectory if provided
        if student_trajectory:
            x_traj = [p.x for p in student_trajectory]
            y_traj = [p.y for p in student_trajectory]
            z_traj = [p.z for p in student_trajectory]
            
            fig.add_trace(go.Scatter3d(
                x=x_traj,
                y=y_traj,
                z=z_traj,
                mode='lines',
                line=dict(
                    color='orange',
                    width=trajectory_width
                ),
                name='Your Path'
            ))
        
        # Update layout for better visualization
        fig.update_layout(
            scene=self._get_default_scene_settings(self.camera_eye_x_right),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='rgba(0, 0, 0, 0.2)',
                borderwidth=1,
                font=dict(size=10)
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=700
        )
        
        return fig

    def animate_dual_trajectories_with_points(self,
                                            depart: Point3D,
                                            arrivee: Point3D,
                                            intermediaire: Optional[Point3D] = None,
                                            exercise_trajectory: List[Point3D] = None,
                                            student_trajectory: List[Point3D] = None,
                                            frame_duration: int = 100) -> go.Figure:
        """
        Create an animated visualization showing both trajectories evolution with fixed points.
        
        Args:
            depart: Starting point
            arrivee: End point
            intermediaire: Optional intermediate point
            exercise_trajectory: List of points for exercise trajectory
            student_trajectory: List of points for student trajectory
            frame_duration: Duration of each frame in milliseconds
        """
        base_figure = self._get_base_figure()
        frames = []
        
        # Add fixed points to each frame
        points_data = [
            (depart, 'red', 'Depart'),
            (arrivee, 'green', 'Arrivée')
        ]
        
        if intermediaire is not None:
            points_data.append((intermediaire, 'blue', 'Intermédiaire'))
        
        # Determine the maximum number of points between both trajectories
        max_points = max(
            len(exercise_trajectory) if exercise_trajectory else 0,
            len(student_trajectory) if student_trajectory else 0
        )
        
        if max_points > 0:
            for i in range(max_points):
                frame_data = list(base_figure.data)
                
                # Add fixed points
                for point, color, label in points_data:
                    frame_data.append(go.Scatter3d(
                        x=[point.x],
                        y=[point.y],
                        z=[point.z],
                        mode='markers',
                        marker=dict(size=8, color=color),
                        name=label
                    ))
                
                # Add growing exercise trajectory
                if exercise_trajectory:
                    current_idx = min(i, len(exercise_trajectory) - 1)
                    frame_data.append(go.Scatter3d(
                        x=[p.x for p in exercise_trajectory[:current_idx + 1]],
                        y=[p.y for p in exercise_trajectory[:current_idx + 1]],
                        z=[p.z for p in exercise_trajectory[:current_idx + 1]],
                        mode='lines',
                        line=dict(color='purple', width=4),
                        name='Exercise Path'
                    ))
                
                # Add growing student trajectory
                if student_trajectory:
                    current_idx = min(i, len(student_trajectory) - 1)
                    frame_data.append(go.Scatter3d(
                        x=[p.x for p in student_trajectory[:current_idx + 1]],
                        y=[p.y for p in student_trajectory[:current_idx + 1]],
                        z=[p.z for p in student_trajectory[:current_idx + 1]],
                        mode='lines',
                        line=dict(color='orange', width=4),
                        name='Your Path'
                    ))
                
                frames.append(go.Frame(data=frame_data, name=f'frame{i}'))
        
        # Create figure with animation controls
        fig = go.Figure(
            data=frames[0].data if frames else base_figure.data,
            frames=frames,
            layout=go.Layout(
                scene=self._get_default_scene_settings(self.camera_eye_x_right),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99,
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='rgba(0, 0, 0, 0.2)',
                    borderwidth=1,
                    font=dict(size=10)
                ),
                updatemenus=[{
                    "buttons": [
                        {
                            "args": [None, {"frame": {"duration": frame_duration},
                                          "fromcurrent": True,
                                          "transition": {"duration": 0}}],
                            "label": "Play",
                            "method": "animate"
                        },
                        {
                            "args": [[None], {"frame": {"duration": 0},
                                            "mode": "immediate",
                                            "transition": {"duration": 0}}],
                            "label": "Pause",
                            "method": "animate"
                        }
                    ],
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                    "xanchor": "right",
                    "yanchor": "bottom"
                }],
                sliders=[{
                    "currentvalue": {"prefix": "Frame: ", "font": {"size": 10}},
                    "len": 0.3,
                    "x": 0.15,
                    "y": 0,
                    "xanchor": "left",
                    "yanchor": "bottom",
                    "steps": [
                        {
                            "args": [[f"frame{k}"], {"frame": {"duration": 0},
                                                   "mode": "immediate",
                                                   "transition": {"duration": 0}}],
                            "label": str(k),
                            "method": "animate"
                        }
                        for k in range(len(frames))
                    ]
                }],
                margin=dict(l=0, r=0, t=30, b=30),
                height=700
            )
        )
        
        return fig
 
# --------------------------
import plotly.graph_objects as go

from dataclasses import dataclass, field
from typing import List, Optional, Union

@dataclass
class VisualizationConfig:
    """Configuration for Bloch sphere visualization parameters."""
    initial_point: Point3D = field(default_factory=lambda: Point3D(0, 0, 1))
    num_intermediate_points: int = 20
    frame_duration: int = 100
    line_color: str = 'black'
    line_width: int = 4
    marker_size: int = 4

@dataclass
class DualVisualizationConfig:
    """Configuration for dual trajectory visualization."""
    initial_point: Point3D = field(default_factory=lambda: Point3D(0, 0, 1))
    num_intermediate_points: int = 20
    frame_duration: int = 100
    is_simultaneous: bool = True
    exercise_color: str = 'blue'
    student_color: str = 'red'
    line_width: int = 4
    marker_size: int = 4


def visualize_bloch_trajectory(
    operations: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    initial_point:Point3D = Point3D(0,0,1),
    config: Optional[VisualizationConfig] = None
) -> None:
    """
    Draw a static visualization of a single quantum state trajectory.
    
    Args:
        operations: List of Bloch operations defining the trajectory
        config: Optional visualization configuration parameters
    """
    config = config or VisualizationConfig()
    visualizer = BlochSphereVisualizer()

    
    fig = visualizer.plot_trajectory(
        trajectory_ops=operations,
        initial_point=initial_point,
        line_color=config.line_color,
        line_width=config.line_width,
        marker_size=config.marker_size
    )
    fig.show()


def animate_bloch_trajectory(
    operations: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    initial_point:Point3D = Point3D(0,0,1),
    num_intermediate_points = 20,
    config: Optional[VisualizationConfig] = None
) -> None:
    """
    Draw a static visualization of a single quantum state trajectory.
    
    Args:
        operations: List of Bloch operations defining the trajectory
        config: Optional visualization configuration parameters
    """
    config = config or VisualizationConfig()
    visualizer = BlochSphereVisualizer()
    
    fig = visualizer.animate_trajectory(trajectory_ops=operations, initial_point=initial_point,
                                        frame_duration=config.frame_duration, line_color=config.line_color,
                                        line_width=config.line_width, marker_size=config.marker_size)
    fig.show()


def visualize_bloch_trajectory_dual(
        exercise_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
        student_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
        initial_point: Point3D,
    config: Optional[DualVisualizationConfig] = None
) -> None:
    """
    Draw a static visualization comparing two quantum state trajectories.
    
    Args:
        operations1: First list of Bloch operations (typically exercise solution)
        operations2: Second list of Bloch operations (typically student solution)
        config: Optional visualization configuration parameters
    """
    config = config or DualVisualizationConfig()
    visualizer = BlochSphereVisualizer()
    
    fig = visualizer.plot_dual_trajectories_static(
        exercise_ops=exercise_ops,
        student_ops=student_ops,
        initial_point=initial_point
    )
    fig.show()


def animate_bloch_trajectory_dual(
        exercise_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
        student_ops: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
        initial_point: Point3D = Point3D(0, 0, 1),
    config: Optional[DualVisualizationConfig] = None
) -> None:
    """
    Draw an animated visualization comparing two quantum state trajectories.
    
    Args:
        operations1: First list of Bloch operations (typically exercise solution)
        operations2: Second list of Bloch operations (typically student solution)
        config: Optional visualization configuration parameters
    """
    config = config or DualVisualizationConfig()
    visualizer = BlochSphereVisualizer()
    
    if config.is_simultaneous:
        fig = visualizer.animate_dual_trajectories_simultaneous(
            exercise_ops=exercise_ops,
            student_ops=student_ops,
            initial_point=initial_point,
            frame_duration=config.frame_duration
        )
    else:
        fig = visualizer.animate_dual_trajectories_sequential(
            exercise_ops=exercise_ops,
            student_ops=student_ops,
            initial_point=initial_point,
            frame_duration=config.frame_duration
        )
    fig.show()

# --------------------------------------

def visualize_bloch_points_and_trajectory(
    depart: Point3D,
    arrivee: Point3D,
    operations: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    intermediaire: Optional[Point3D] = None,
    config: Optional[VisualizationConfig] = None
) -> None:
    """
    Draw a static visualization of a single quantum state trajectory.
    
    Args:
        operations: List of Bloch operations defining the trajectory
        config: Optional visualization configuration parameters
    """
    config = config or VisualizationConfig()
    visualizer = PointsBlochSphereVisualizer()
    
    if isinstance(operations, list) and all(isinstance(op, BlochOperation) for op in operations):
        trajectory_points, trajectory_colors = generate_optimized_trajectory(
                                                start_point=depart,
                                                operations=operations, 
                                                num_intermediate_points=config.num_intermediate_points
                                                )
    else:
        trajectory_points, trajectory_colors = operations
    

    fig = visualizer.plot_points_and_trajectory(
        depart=depart,
        arrivee=arrivee,
        intermediaire=intermediaire,
        trajectory_points=trajectory_points,
        trajectory_width=config.line_width,
        point_size=8
        )
    fig.show()


def animate_bloch_points_and_trajectory(
    depart: Point3D,
    arrivee: Point3D,
    operations: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    intermediaire: Optional[Point3D] = None,
    config: Optional[VisualizationConfig] = None
) -> None:
    """
    Draw a static visualization of a single quantum state trajectory.
    
    Args:
        operations: List of Bloch operations defining the trajectory
        config: Optional visualization configuration parameters
    """
    config = config or VisualizationConfig()
    visualizer = PointsBlochSphereVisualizer()
    
    if isinstance(operations, list) and all(isinstance(op, BlochOperation) for op in operations):
        trajectory_points, trajectory_colors = generate_optimized_trajectory(
                                                start_point=depart,
                                                operations=operations, 
                                                num_intermediate_points=config.num_intermediate_points
                                                )
    else:
        trajectory_points, trajectory_colors = operations
    
    
    fig = visualizer.animate_trajectory_with_points(
        depart=depart,
        arrivee=arrivee,
        intermediaire=intermediaire,
        trajectory_points=trajectory_points,
        frame_duration=100
        )
    fig.show()


def visualize_bloch_points_and_trajectory_dual(
    depart: Point3D,
    arrivee: Point3D,
    operations1: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    operations2: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    intermediaire: Optional[Point3D] = None,
    config: Optional[DualVisualizationConfig] = None
) -> None:
    """
    Draw a static visualization comparing two quantum state trajectories.
    
    Args:
        operations1: First list of Bloch operations (typically exercise solution)
        operations2: Second list of Bloch operations (typically student solution)
        config: Optional visualization configuration parameters
    """
    config = config or DualVisualizationConfig()
    visualizer = PointsBlochSphereVisualizer()

    if isinstance(operations1, list) and all(isinstance(op, BlochOperation) for op in operations1):
        trajectory_points_op1, trajectory_colors_op1 = generate_optimized_trajectory(
                                                start_point=depart,
                                                operations=operations1, 
                                                num_intermediate_points=config.num_intermediate_points
                                                )
    else:
        trajectory_points_op1, trajectory_colors_op1 = operations1

    
    if isinstance(operations2, list) and all(isinstance(op, BlochOperation) for op in operations2):
        trajectory_points_op2, trajectory_colors_op2 = generate_optimized_trajectory(
                                                start_point=depart,
                                                operations=operations2, 
                                                num_intermediate_points=config.num_intermediate_points
                                                )
    else:
        trajectory_points_op2, trajectory_colors_op2 = operations2


    fig = visualizer.plot_points_and_dual_trajectories(
        depart=depart,
        arrivee=arrivee,
        intermediaire=intermediaire,
        exercise_trajectory=trajectory_points_op1,
        student_trajectory=trajectory_points_op2
        )
    fig.show()


def animate_bloch_points_and_trajectory_dual(
    depart: Point3D,
    arrivee: Point3D,
    operations1: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    operations2: Union[List[BlochOperation], Tuple[List[Point3D], List[str]]],
    intermediaire: Optional[Point3D] = None,
    config: Optional[DualVisualizationConfig] = None
) -> None:
    """
    Draw a static visualization comparing two quantum state trajectories.
    
    Args:
        operations1: First list of Bloch operations (typically exercise solution)
        operations2: Second list of Bloch operations (typically student solution)
        config: Optional visualization configuration parameters
    """
    config = config or DualVisualizationConfig()
    visualizer = PointsBlochSphereVisualizer()
    
    if isinstance(operations1, list) and all(isinstance(op, BlochOperation) for op in operations1):
        trajectory_points_op1, trajectory_colors_op1 = generate_optimized_trajectory(
                                                start_point=depart,
                                                operations=operations1, 
                                                num_intermediate_points=config.num_intermediate_points
                                                )
    else:
        trajectory_points_op1, trajectory_colors_op1 = operations1

    
    if isinstance(operations2, list) and all(isinstance(op, BlochOperation) for op in operations2):
        trajectory_points_op2, trajectory_colors_op2 = generate_optimized_trajectory(
                                                start_point=depart,
                                                operations=operations2, 
                                                num_intermediate_points=config.num_intermediate_points
                                                )
    else:
        trajectory_points_op2, trajectory_colors_op2 = operations2


    fig = visualizer.animate_dual_trajectories_with_points(
        depart=depart,
        arrivee=arrivee,
        intermediaire=intermediaire,
        exercise_trajectory=trajectory_points_op1,
        student_trajectory=trajectory_points_op2
        )
    fig.show()


 # dictionary with remarkable quantum states


# ---------------------------------------
# ---------------------------------------
# Example usage:
def test_points_bloch_sphere():
    # Create test points
    depart = QUANTUM_STATES_Point3D["0"]
    arrivee = QUANTUM_STATES_Point3D["1"]
    intermediaire = QUANTUM_STATES_Point3D["+"]
    
    # test trajectory operations
    trajectory_operations = [
        BlochGate.H_gate(),
        BlochGate.Z_gate(),
        BlochGate.H_gate()
        ]
    
    config = VisualizationConfig(initial_point=depart)

    # Create static visualization
    visualize_bloch_points_and_trajectory(depart=depart, arrivee=arrivee, operations=trajectory_operations, config=config)

    # Create animated visualization
    animate_bloch_points_and_trajectory(depart=depart, arrivee=arrivee, operations=trajectory_operations, config=config)


def test_points_bloch_sphere_dual():
        # Create test points
    depart = QUANTUM_STATES_Point3D["0"]
    arrivee = QUANTUM_STATES_Point3D["1"]
    intermediaire = QUANTUM_STATES_Point3D["+"]
    
    # test trajectory operations
    trajectory_operations1 = [
        BlochGate.H_gate(),
        BlochGate.Z_gate(),
        BlochGate.H_gate()
        ]
    
    trajectory_operations2 = [
        BlochGate.H_gate(),
        BlochGate.T_gate(),
        BlochGate.H_gate()
        ]
    
    config = VisualizationConfig(initial_point=depart)

    
    # Create static visualization
    visualize_bloch_points_and_trajectory_dual(
        depart=depart,
        arrivee=arrivee,
        intermediaire=intermediaire,
        operations1=trajectory_operations1,
        operations2=trajectory_operations2
        )

    # Create animated visualization
    animate_bloch_points_and_trajectory_dual(
        depart=depart,
        arrivee=arrivee,
        intermediaire=intermediaire,
        operations1=trajectory_operations1,
        operations2=trajectory_operations2
        )


# ------------------
# Test:
def test_exo_1():
    operations = [
        BlochGate.Rx(np.pi / 4),
        BlochGate.H_gate(),
        BlochGate.Rz(np.pi / 3)
    ]
    return operations

def test_student_1():
    operations = [
        BlochGate.Rx(np.pi / 3),
        BlochGate.H_gate(),
        BlochGate.Rz(np.pi / 2)
    ]
    return operations

def test_single_plot_anime():
    visualize_bloch_trajectory(test_exo_1())

    visualize_bloch_trajectory(test_exo_1(), initial_point=Point3D(0,1,0))

    animate_bloch_trajectory(test_exo_1())

    animate_bloch_trajectory(test_exo_1(), initial_point=Point3D(1,0,0))

def test_dual_plot_anime():
    list_op1 = test_exo_1()
    list_op2 = test_student_1()

    visualize_bloch_trajectory_dual(list_op1, list_op2)

    animate_bloch_trajectory_dual(list_op1, list_op2)

    config = DualVisualizationConfig(num_intermediate_points=20, is_simultaneous=False)
    animate_bloch_trajectory_dual(list_op1, list_op2, config=config)

# --------------------
# Part for the challenge:
# this part is not part of the core, it used only in the challange, after it will be removed
import pickle

def load_data_from_pickle(filename='exercise_trajectories.pkl'):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    return data


@dataclass
class ExercisePoints:
    start: Point3D
    arrive: Point3D
    intermediate: Point3D
    operations: List[BlochOperation]

# -------------------
# save animation and figure:
import numpy as np
import plotly.graph_objs as go
import imageio
import os
from time import sleep

from tqdm import tqdm
import shutil
import os
import shutil
from PIL import Image
import io
import base64

def _save_animation(fig, filename, format='gif', duration=100, fps=10, width=800, height=800):
    """
    Saves the Bloch sphere animation using PIL for image processing.
    
    Parameters:
    fig: plotly figure object with animation
    filename: str, output filename (without extension)
    format: str, output format ('gif', 'html', or 'png')
    duration: int, duration of each frame in milliseconds (for gif)
    fps: int, frames per second (for gif)
    width/height: int, dimensions in pixels
    """
    
    # Create results directory
    result_dir = "result_animation"
    os.makedirs(result_dir, exist_ok=True)
    base_path = os.path.join(result_dir, filename)

    if format == 'gif':
        print(f"\nProcessing animation: {filename}")
        temp_dir = os.path.join(result_dir, "temp_frames")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Step 1: Save frames using PIL
            print("\nStep 1/3: Generating frames...")
            frames = []
            pil_frames = []
            
            for i in tqdm(range(len(fig.frames))):
                # Update figure with frame data
                fig.update(data=fig.frames[i].data)
                
                # Convert plotly figure to PNG bytes
                img_bytes = fig.to_image(format='png', 
                                       width=width, 
                                       height=height)
                
                # Convert bytes to PIL Image
                img = Image.open(io.BytesIO(img_bytes))
                pil_frames.append(img)
                
                # Optionally save frame
                frame_path = os.path.join(temp_dir, f"frame_{i:03d}.png")
                img.save(frame_path)
                frames.append(frame_path)
            
            # Step 2: Create GIF using PIL
            print("\nStep 2/3: Creating GIF...")
            gif_path = f"{base_path}.gif"
            
            # Save as GIF using PIL
            pil_frames[0].save(
                gif_path,
                save_all=True,
                append_images=pil_frames[1:],
                optimize=True,
                duration=duration,
                loop=0
            )
            
            print(f"\n✓ Successfully saved GIF to: {gif_path}")
            return gif_path

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    elif format == 'html':
        print(f"\nSaving HTML animation: {filename}")
        output_path = f"{base_path}.html"
        fig.write_html(output_path)
        print(f"✓ Successfully saved HTML to: {output_path}")
        return output_path

    elif format == 'png':
        print(f"\nSaving final frame as PNG: {filename}")
        output_path = f"{base_path}.png"
        
        # Update to last frame if animation exists
        if fig.frames:
            fig.update(data=fig.frames[-1].data)
            
        # Convert to PNG using PIL
        img_bytes = fig.to_image(format='png', 
                               width=width, 
                               height=height)
        img = Image.open(io.BytesIO(img_bytes))
        img.save(output_path)
        
        print(f"✓ Successfully saved PNG to: {output_path}")
        return output_path

    else:
        raise ValueError("Format must be 'gif', 'html', or 'png'")

# -------------------------------------
# new version, since the previous crash ...

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import os
from tqdm import tqdm
from mpl_toolkits.mplot3d import Axes3D
from typing import List, Union, Tuple, Optional

def save_bloch_animation(fig, filename="bloch_animation", format='gif', duration=100, fps=10, width=800, height=800, camera_eye=None):
    """
    Saves Bloch sphere animations using matplotlib, matching the BlochSphereVisualizer style.
    
    Parameters:
    fig: plotly figure object from animate_trajectory
    filename: str, output filename (without extension)
    format: str, output format ('gif' or 'png')
    duration: int, duration of each frame in milliseconds
    fps: int, frames per second
    width/height: int, dimensions in pixels
    camera_eye: dict, camera position (e.g., {"x": 1.5, "y": 1.5, "z": 1})
    """
    
    # Create results directory
    result_dir = "result_animation"
    os.makedirs(result_dir, exist_ok=True)
    base_path = os.path.join(result_dir, filename)
    
    def create_sphere_mesh(phi_points=20, theta_points=40):
        """Create Bloch sphere wireframe matching the original visualizer"""
        phi = np.linspace(0, np.pi, phi_points)
        theta = np.linspace(0, 2 * np.pi, theta_points)
        
        x_lines, y_lines, z_lines = [], [], []
        
        # Create meridians
        for t in theta:
            x_meridian = np.sin(phi) * np.cos(t)
            y_meridian = np.sin(phi) * np.sin(t)
            z_meridian = np.cos(phi)
            x_lines.append(x_meridian)
            y_lines.append(y_meridian)
            z_lines.append(z_meridian)
        
        # Create parallels
        for p in phi[1:-1]:  # Skip poles
            x_parallel = np.sin(p) * np.cos(theta)
            y_parallel = np.sin(p) * np.sin(theta)
            z_parallel = np.cos(p) * np.ones_like(theta)
            x_lines.append(x_parallel)
            y_lines.append(y_parallel)
            z_lines.append(z_parallel)
            
        return x_lines, y_lines, z_lines
    
    def extract_trajectory_data(frame):
        """Extract trajectory data from a Plotly frame"""
        # The last trace contains the trajectory data
        trajectory_data = frame.data[-1]
        return (
            np.array(trajectory_data.x),
            np.array(trajectory_data.y),
            np.array(trajectory_data.z),
            trajectory_data.line.color if hasattr(trajectory_data.line, 'color') else 'black',
            trajectory_data.marker.color if hasattr(trajectory_data.marker, 'color') else None
        )
    
    def setup_bloch_sphere(ax):
        """Set up the Bloch sphere with matching style"""
        # Plot sphere wireframe
        x_lines, y_lines, z_lines = create_sphere_mesh()
        for x, y, z in zip(x_lines, y_lines, z_lines):
            ax.plot(x, y, z, color='gray', alpha=0.3, linewidth=1)
        
        # Add axes
        axis_length = 1.2
        axes = [(axis_length, 0, 0), (0, axis_length, 0), (0, 0, axis_length)]
        colors = ['red', 'green', 'blue']
        labels = ['x', 'z']
        
        for (x, y, z), color, label in zip(axes, colors, labels):
            ax.plot([0, x], [0, y], [0, z], color=color, linewidth=3, label=label)
        
        # Set labels and limits
        ax.set_xlabel('X')
        ax.set_zlabel('Z')
        ax.set_xlim([-1.2, 1.2])
        ax.set_ylim([-1.2, 1.2])
        ax.set_zlim([-1.2, 1.2])
        
        # Set view angle if provided
        if camera_eye:
            ax.view_init(
                elev=np.arctan2(camera_eye['z'], np.sqrt(camera_eye['x']**2 + camera_eye['y']**2)) * 180/np.pi,
                azim=np.arctan2(camera_eye['y'], camera_eye['x']) * 180/np.pi
            )
    
    def create_frame(frame_idx):
        ax.clear()
        setup_bloch_sphere(ax)
        
        # Get trajectory data for this frame
        x, y, z, line_color, point_colors = extract_trajectory_data(fig.frames[frame_idx])
        
        # Plot trajectory line
        if len(x) > 1:
            ax.plot(x, y, z, color=line_color, linewidth=4)
        
        # Handle point colors
        if isinstance(point_colors, (list, np.ndarray)) and len(point_colors) != len(x):
            # If colors array length doesn't match points, use single color
            point_colors = line_color
        
        # Plot points
        ax.scatter(x, y, z, c=point_colors if point_colors is not None else line_color, s=40)
    
    if format == 'gif':
        print(f"\nProcessing animation: {filename}")
        
        # Create figure and 3D axes
        plt_fig = plt.figure(figsize=(width/100, height/100), dpi=100)
        ax = plt_fig.add_subplot(111, projection='3d')
        
        # Create animation
        frames = len(fig.frames)
        anim = FuncAnimation(
            plt_fig, 
            create_frame,
            frames=frames,
            interval=duration
        )
        
        # Save as GIF
        gif_path = f"{base_path}.gif"
        writer = PillowWriter(fps=fps)
        anim.save(gif_path, writer=writer)
        
        plt.close()
        print(f"\n✓ Successfully saved GIF to: {gif_path}")
        return gif_path
        
    elif format == 'png':
        print(f"\nSaving final frame as PNG: {filename}")
        
        # Create figure and plot final frame
        plt_fig = plt.figure(figsize=(width/100, height/100), dpi=100)
        ax = plt_fig.add_subplot(111, projection='3d')
        create_frame(-1)  # Plot last frame
        
        # Save as PNG
        output_path = f"{base_path}.png"
        plt_fig.savefig(output_path)
        plt.close()
        
        print(f"✓ Successfully saved PNG to: {output_path}")
        return output_path
    
    else:
        raise ValueError("Format must be 'gif' or 'png'")
    
    # this also, have pbm , a bug ....

# --------------------------------------

def generate_and_save_animation(operations, 
                                initial_point=Point3D(0,0,1),
                                is_camera_eye_x_right=False, 
                                num_intermediate_points=5,
                                frame_duration=80,
                                line_color="black",
                                file_name="bloch_animation_gif"):
    visualizer = BlochSphereVisualizer()

    trajectory_points_colors = generate_optimized_trajectory(start_point=initial_point, operations=operations,num_intermediate_points=num_intermediate_points)

    fig = visualizer.animate_trajectory(
        trajectory_ops=trajectory_points_colors,
        initial_point=initial_point, 
        frame_duration=frame_duration, 
        is_camera_eye_x_right=is_camera_eye_x_right,
        line_color=line_color)
    # fig.show()
    path = _save_animation(fig, file_name, format="gif") # sometimes work, and other Noooooo
    
    # Use the camera eye position from your visualizer
    #camera_eye = (visualizer.camera_eye_x_right if is_camera_eye_x_right else visualizer.camera_eye_default)
    # path = save_bloch_animation(fig, file_name, format="gif",camera_eye=camera_eye)

    print(" bloch_animation_gif saved to : ", path)


def test_generate_and_save_animation():
    operations = test_exo_1()
    generate_and_save_animation(operations, 
                                is_camera_eye_x_right=False, 
                                num_intermediate_points=10,
                                frame_duration=80,
                                line_color="black")


def main():
    # test_points_bloch_sphere() # test ok
    # test_points_bloch_sphere_dual() # test ok
    
    # test_single_plot_anime() # test ok
    # test_dual_plot_anime() # test ok

    test_generate_and_save_animation()
    


# Example usage
if __name__ == "__main__":
    main()


# Todo: handle the phase color
# when apply X gate on 0, we go to 1 (on bloch sphere from top (0,0,1) to down (0,0,-1))
# the color of the trajjectory is red for example.
# now if we applay z gate, in quantum state, we change the phase from 1 to -1.
# but on the block sphere we don't move, I want to add somthing visual to indicate that the phase is changed
# maybe add - sign as label at the end of trajectory
# mayb change the color of trajectory for some color to indcate that.
