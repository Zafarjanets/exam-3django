from ultralytics import YOLO

model = YOLO("yolov8n.pt")


def detect_products(image_path):
    results = model(image_path)

    names = []
    print(results)

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = model.names[cls_id]
            names.append(name)

    return list(set(names))