import cv2
import pickle
import numpy as np
import time

from collections import deque, Counter
from insightface.app import FaceAnalysis

from attendance import check_employee_attendance


# ============================================================
# SETTINGS
# ============================================================

EMBEDDINGS_FILE = "data/embeddings/face_embeddings.pkl"

# Minimum similarity required to consider a face a match
SIMILARITY_THRESHOLD = 0.45

# InsightFace detection resolution
DETECTION_SIZE = (320, 320)

# Run AI every 5 frames instead of every frame
PROCESS_EVERY_N_FRAMES = 5

# Number of recent predictions to remember
HISTORY_SIZE = 5

# Number of matching predictions required
# before considering recognition confirmed
REQUIRED_MATCHES = 3

# Prevent repeated attendance processing
# for the same employee within this period
ATTENDANCE_COOLDOWN = 30


# ============================================================
# LOAD EMPLOYEE EMBEDDINGS
# ============================================================

with open(EMBEDDINGS_FILE, "rb") as file:
    employee_embeddings = pickle.load(file)


print("Loaded employee embeddings:")
print(employee_embeddings.keys())


# ============================================================
# LOAD INSIGHTFACE
# ============================================================

app = FaceAnalysis(name="buffalo_l")

app.prepare(
    ctx_id=-1,
    det_size=DETECTION_SIZE
)


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(0)

camera.set(
    cv2.CAP_PROP_BUFFERSIZE,
    1
)


# ============================================================
# RECOGNITION STATE
# ============================================================

prediction_history = deque(
    maxlen=HISTORY_SIZE
)

latest_results = []

frame_count = 0


# Stores the last time attendance was processed
# for each employee.

last_attendance_time = {}


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):

    a = np.asarray(
        a,
        dtype=np.float32
    ).reshape(-1)

    b = np.asarray(
        b,
        dtype=np.float32
    ).reshape(-1)

    return float(
        np.dot(a, b)
    )


# ============================================================
# FIND EMPLOYEE
# ============================================================

def find_employee(face_embedding):

    best_employee = None

    best_similarity = -1.0


    # Convert live embedding into
    # a one-dimensional vector.

    face_vector = np.asarray(
        face_embedding,
        dtype=np.float32
    ).reshape(-1)


    # Go through all registered employees.

    for employee_id, embeddings in employee_embeddings.items():

        stored_vectors = np.asarray(
            embeddings,
            dtype=np.float32
        )


        # ----------------------------------------------------
        # CASE 1:
        # Employee has one embedding
        #
        # Shape:
        # (512,)
        # ----------------------------------------------------

        if stored_vectors.ndim == 1:

            similarity = cosine_similarity(
                face_vector,
                stored_vectors
            )

            similarity = float(
                similarity
            )


            if similarity > best_similarity:

                best_similarity = similarity

                best_employee = employee_id


        # ----------------------------------------------------
        # CASE 2:
        # Employee has multiple embeddings
        #
        # Shape:
        # (N, 512)
        # ----------------------------------------------------

        else:

            for stored_vector in stored_vectors:

                similarity = cosine_similarity(
                    face_vector,
                    stored_vector
                )

                similarity = float(
                    similarity
                )


                if similarity > best_similarity:

                    best_similarity = similarity

                    best_employee = employee_id


    # --------------------------------------------------------
    # CHECK SIMILARITY THRESHOLD
    # --------------------------------------------------------

    if best_similarity >= SIMILARITY_THRESHOLD:

        return (
            best_employee,
            best_similarity
        )


    return (
        None,
        best_similarity
    )


# ============================================================
# MAIN CAMERA LOOP
# ============================================================

while True:

    success, frame = camera.read()


    # --------------------------------------------------------
    # CAMERA ERROR
    # --------------------------------------------------------

    if not success:

        print(
            "Could not access camera"
        )

        break


    frame_count += 1


    # ========================================================
    # RUN AI EVERY N FRAMES
    # ========================================================

    if (
        frame_count %
        PROCESS_EVERY_N_FRAMES
        == 0
    ):

        faces = app.get(frame)

        current_results = []


        # ====================================================
        # PROCESS EVERY DETECTED FACE
        # ====================================================

        for face in faces:


            # ------------------------------------------------
            # FIND EMPLOYEE
            # ------------------------------------------------

            employee_id, similarity = find_employee(
                face.normed_embedding
            )


            # =================================================
            # EMPLOYEE MATCH FOUND
            # =================================================

            if employee_id is not None:


                # Add prediction to history

                prediction_history.append(
                    employee_id
                )


                # Count recent predictions

                counts = Counter(
                    prediction_history
                )


                most_common_employee, count = (
                    counts.most_common(1)[0]
                )


                # ------------------------------------------------
                # CHECK MULTI-FRAME CONFIRMATION
                # ------------------------------------------------

                if count >= REQUIRED_MATCHES:

                    confirmed_employee = (
                        most_common_employee
                    )

                    status = "CONFIRMED"


                    # ============================================
                    # ATTENDANCE COOLDOWN
                    # ============================================

                    current_time_seconds = time.time()


                    last_time = (
                        last_attendance_time.get(
                            confirmed_employee,
                            0
                        )
                    )


                    # Only process attendance if
                    # cooldown has expired.

                    if (
                        current_time_seconds
                        - last_time
                        >= ATTENDANCE_COOLDOWN
                    ):

                        check_employee_attendance(
                            confirmed_employee
                        )


                        # Remember when we processed
                        # attendance for this employee.

                        last_attendance_time[
                            confirmed_employee
                        ] = current_time_seconds


                else:

                    confirmed_employee = (
                        employee_id
                    )

                    status = "Checking..."


            # =================================================
            # NO EMPLOYEE MATCH
            # =================================================

            else:

                # Clear previous employee predictions.

                prediction_history.clear()


                confirmed_employee = "Unknown"

                status = "Unknown"


            # =================================================
            # GET FACE BOX
            # =================================================

            x1, y1, x2, y2 = map(
                int,
                face.bbox
            )


            # =================================================
            # STORE RESULT
            # =================================================

            current_results.append(
                (
                    x1,
                    y1,
                    x2,
                    y2,
                    confirmed_employee,
                    similarity,
                    status
                )
            )


        # Store latest AI results

        latest_results = current_results


    # ========================================================
    # DRAW RESULTS ON CAMERA
    # ========================================================

    for (
        x1,
        y1,
        x2,
        y2,
        employee_id,
        similarity,
        status
    ) in latest_results:


        # ----------------------------------------------------
        # DRAW FACE BOX
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )


        # ----------------------------------------------------
        # CREATE LABEL
        # ----------------------------------------------------

        label = (
            f"{employee_id} | "
            f"{similarity:.2f} | "
            f"{status}"
        )


        # ----------------------------------------------------
        # DRAW LABEL
        # ----------------------------------------------------

        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )


    # ========================================================
    # SHOW CAMERA
    # ========================================================

    cv2.imshow(
        "Employee Attendance System",
        frame
    )


    # ========================================================
    # PRESS Q TO EXIT
    # ========================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()