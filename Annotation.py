#annotates the video from the csv file
import os
import csv
import cv2
import ast

def read_csv_data(filename, video_file_name):
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            if row[0] == video_file_name:  # Match video file name
                print(f"Matched row for {video_file_name}: {row}")  # Debugging: print the row
                try:
                    scale_point1 = ast.literal_eval(row[1])
                    scale_point2 = ast.literal_eval(row[2])
                    point1 = ast.literal_eval(row[3]) if row[3] != "Default Value" else None
                    point2 = ast.literal_eval(row[4])
                    point3 = ast.literal_eval(row[5])
                    takeoff = ast.literal_eval(row[6])
                    land = ast.literal_eval(row[7])
                    angle_point1 = ast.literal_eval(row[9])
                    angle_point2 = ast.literal_eval(row[10])
                    points = [p for p in [point1, point2, point3] if p is not None]

                    op_name=row[-1]
                    # Parse the frame numbers
                    #frame_numbers = ast.literal_eval(row[-1]) if row[-1].strip() else []
                    frame_numbers = ast.literal_eval(row[20])

                    return points, [scale_point1, scale_point2], [takeoff, land], [angle_point1, angle_point2], frame_numbers
                except ValueError as e:
                    print(f"Error parsing row for {video_file_name}: {e}")
                    return [], [], [], [], []
    return [], [], [], [], []
def draw_markers(frame, points, color, radius=5, thickness=-1):
    for point in points:
        cv2.circle(frame, point, radius, color, thickness)

def draw_horizontal_lines_with_points(frame, point_pairs, point_color, line_color, point_radius=5, line_thickness=2):
    for point_pair in point_pairs:
        x1, y1 = point_pair[0]
        x2, y2 = point_pair[1]
        cv2.line(frame, (x1, y1), (x2, y1), line_color, line_thickness)
        cv2.circle(frame, (x1, y1), point_radius, point_color, -1)
        cv2.circle(frame, (x2, y1), point_radius, point_color, -1)

def draw_line_w_points(frame, point_pairs, point_color, line_color, point_radius=5, line_thickness=2):
    for point_pair in point_pairs:
        x1, y1 = point_pair[0]
        x2, y2 = point_pair[1]
        cv2.line(frame, (x1, y1), (x2, y2), line_color, line_thickness)
        cv2.line(frame, (x1, y1), (x2, y1), line_color, line_thickness)
        cv2.circle(frame, (x1, y1), point_radius, point_color, -1)
        cv2.circle(frame, (x2, y2), point_radius, point_color, -1)
        cv2.circle(frame, (x2, y1), point_radius, point_color, -1)

def process_video(input_video_path, output_video_path, points, scale_points, jump_points, angle_points, frame_numbers):
    cap = cv2.VideoCapture(input_video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        output_video_path, 
        fourcc, 
        cap.get(cv2.CAP_PROP_FPS), 
        (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    )
    
    # Ensure frame_numbers is valid
    if len(frame_numbers) < 9:
        print(f"Error: Expected 9 frame numbers, but got {len(frame_numbers)}")
        cap.release()
        out.release()
        return

    # Track which points should be drawn after specific frames
    stride_drawn = False
    takeoff_land_drawn = False
    angle_drawn = False

    current_frame = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Always draw the scale points
        draw_horizontal_lines_with_points(frame, [scale_points], (0, 0, 0), (0, 0, 0))

        # Draw stride points based on how many are available
        if len(points) == 2:
            # Only two strides
            if current_frame >= frame_numbers[3] and not stride_drawn:
                draw_markers(frame, points[:1], (255, 0, 0))
            if current_frame >= frame_numbers[4] and not stride_drawn:
                draw_markers(frame, points[:2], (255, 0, 0))
                stride_drawn = True
            elif stride_drawn:
                draw_markers(frame, points, (255, 0, 0))
        elif len(points) == 3:
            # Three strides
            if current_frame >= frame_numbers[2] and not stride_drawn:
                draw_markers(frame, points[:1], (255, 0, 0))
            if current_frame >= frame_numbers[3] and not stride_drawn:
                draw_markers(frame, points[:2], (255, 0, 0))
            if current_frame >= frame_numbers[4] and not stride_drawn:
                draw_markers(frame, points, (255, 0, 0))
                stride_drawn = True
            elif stride_drawn:
                draw_markers(frame, points, (255, 0, 0))

        # Once the takeoff and landing points are drawn, keep them for the rest of the video
        if current_frame >= frame_numbers[5] and current_frame >= frame_numbers[6] and not takeoff_land_drawn:
            draw_horizontal_lines_with_points(frame, [jump_points], (0, 0, 255), (0, 0, 255))
            takeoff_land_drawn = True
        elif takeoff_land_drawn:
            draw_horizontal_lines_with_points(frame, [jump_points], (0, 0, 255), (0, 0, 255))

        # Once the angle points are drawn, keep them for the rest of the video
        if current_frame >= frame_numbers[7] and current_frame >= frame_numbers[8] and not angle_drawn:
            draw_line_w_points(frame, [angle_points], (255, 255, 0), (255, 255, 0))
            angle_drawn = True
        elif angle_drawn:
            draw_line_w_points(frame, [angle_points], (255, 255, 0), (255, 255, 0))

        out.write(frame)
        current_frame += 1

    cap.release()
    out.release()
    print(f"Video saved as {output_video_path}")
# Other helper functions remain the same

def process_folder(video_folder, output_folder, csv_file):
    for video_file_name in os.listdir(video_folder):
        if video_file_name.endswith(('.mp4', '.MOV', '.avi', '.mov')):  # Adjust for valid video extension
            video_id = os.path.splitext(video_file_name)[0][-12:]  # Extract video ID
            output_video_path = os.path.join(output_folder, f"{os.path.splitext(video_id)[0]}_csv.mp4")

            # Check if the output video already exists
            if os.path.exists(output_video_path):
                print(f"Skipping {video_id}: Output video already exists.")
                continue  # Skip to the next video

            input_video_path = os.path.join(video_folder, video_file_name)
            points, scale_points, jump_points, angle_points, frame_numbers = read_csv_data(csv_file, video_id)
            
            if not frame_numbers:  # If frame_numbers is empty, skip this video
                print(f"Skipping {video_id}: No frame numbers found.")
                continue  # Skip to the next video

            if points:
                print(f"Processing {video_id}...")
                process_video(input_video_path, output_video_path, points, scale_points, jump_points, angle_points, frame_numbers)
            else:
                print(f"No matching data for {video_id} in CSV.")

def main():
    video_folder = r "ADD input folder"
    output_folder = r"ADD output folder"
    csv_file = r"ADD csv path"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    process_folder(video_folder, output_folder, csv_file)

if __name__ == "__main__":
    main()
    print("Batch processing complete")
