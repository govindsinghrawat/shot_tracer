import cv2, time
import numpy as np
from scipy.interpolate import interp1d

class ShotTracer:
    def __init__(self, video_path, output_path, line_thickness=5, line_alpha=0.5):
        self.video_path = video_path
        self.output_path = output_path
        self.coordinates = {}  # Dictionary to store coordinates for each frame
        self.frame_count = None
        self.current_frame = 0
        self.line_color = (255, 255, 255)  # Default line color
        self.line_thickness = line_thickness  # Default line thickness
        self.line_roundness = 10  # Default line roundness
        self.start_frame = None
        self.end_frame = None
        self.line_alpha = line_alpha  # Transparency of the tracking line

    def _on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"Clicked on frame {self.current_frame}: ({x}, {y})")
            if self.start_frame is None:
                self.start_frame = self.current_frame
            self.coordinates[self.current_frame] = (x, y)
            self.end_frame = self.current_frame

    def _interpolate_points(self):
        if self.start_frame is None or self.end_frame is None or len(self.coordinates) < 2:
            return {}

        frames = list(range(self.start_frame, self.end_frame + 1))
        x_values = []
        y_values = []
        for frame_num, (x, y) in sorted(self.coordinates.items()):
            x_values.append(x)
            y_values.append(y)

        #interpolator = interp1d(list(self.coordinates.keys()), [x_values, y_values], kind='linear')
#         interpolator = interp1d(list(self.coordinates.keys()), [x_values, y_values], kind='cubic')
        interpolator = interp1d(list(self.coordinates.keys()), [x_values, y_values], kind='quadratic')
        interpolated_points = {}
        for frame_num in range(self.start_frame, self.end_frame + 1):
            interpolated_points[frame_num] = (int(interpolator(frame_num)[0]), int(interpolator(frame_num)[1]))

        #print("Interpolated points:", interpolated_points)  # Print interpolated points for debugging
        return interpolated_points

    def _draw_smooth_curve(self, frame, interpolated_points):

        prev_coordinate = None
        start_frame = min(interpolated_points.keys())  # Find the start frame of the interpolated points
        end_frame = max(interpolated_points.keys())    # Find the end frame of the interpolated points

        for frame_num in range(start_frame, end_frame + 1):
            if frame_num > self.current_frame:  # Stop drawing if the frame number exceeds the current frame
                break
            if frame_num in interpolated_points:
                x, y = interpolated_points[frame_num]
                if prev_coordinate:
                    cv2.line(frame, prev_coordinate, (x, y), self.line_color, self.line_thickness)  # Draw line with default color and thickness
                cv2.circle(frame, (x, y), 3, self.line_color, -1)  # Draw circle with default color
                prev_coordinate = (x, y)

    def _capture_coordinates(self):
        cv2.namedWindow('Video')
        cv2.setMouseCallback('Video', self._on_mouse_click)

        cap = cv2.VideoCapture(self.video_path)
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow('Video', frame)
            self.current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

            key = cv2.waitKey(0)

            if key == ord('x'):  # End coordinate capturing process
                break

        cap.release()
        cv2.destroyAllWindows()
        time.sleep(2)

    def trace_shot(self):
        self._capture_coordinates()
        print("Tracing shot")

        interpolated_points = self._interpolate_points()

        cap = cv2.VideoCapture(self.video_path)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (frame_width, frame_height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            self.current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            overlay = frame.copy()  # Create overlay image
            self._draw_smooth_curve(overlay, interpolated_points)  # Draw the traced path on the overlay
            result = cv2.addWeighted(overlay, self.line_alpha, frame, 1 - self.line_alpha, 0)  # Blend overlay with original frame
            cv2.putText(result, f'Frame: {self.current_frame}/{self.frame_count}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, self.line_color, 2, cv2.LINE_AA)
            out.write(result)
            cv2.imshow('Video', result)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to stop playing the video
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    #input_video_path = input("Enter the absolute path to the input video file: ")
    input_video_path="../input/IMG_8413.MOV"
    #output_video_path = input("Enter the absolute path to save the output video file: ")
    output_video_path="../output/IMG_8413_7777777.avi"
    shot_tracer = ShotTracer(input_video_path, output_video_path, line_thickness=15, line_alpha=0.60)
    shot_tracer.trace_shot()
