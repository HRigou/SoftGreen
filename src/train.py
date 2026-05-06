from ultralytics import YOLO

def train():
    model = YOLO("yolov8n.pt")
    model.train(
        data="data/yolo_dataset/data.yaml",
        epochs=50,
        imgsz=640,
    )

if __name__ == "__main__":
    train()
