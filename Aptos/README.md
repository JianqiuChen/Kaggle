

    Network : EfficientNetB4& EfficientNetB5 (Both Classification and regression.)

    Image size: B4: (256x256), B5: (328x328)

    Image Preprocessing: Cropping images Only.
    (Code from https://www.kaggle.com/benjaminwarner/starter-code-resized-15-19-blindness-images)

    Data Augment:
    train_transform = transforms.Compose([ transforms.ColorJitter(brightness=0.45, contrast=0.45), transforms.RandomAffine(degrees=360, scale=(1.0, 1.3)), transforms.RandomHorizontalFlip(), transforms.RandomVerticalFlip(), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    Optimizer : Adam

    Loss : Classification: Cross entropy Loss
    Regression:MSE

    Learning Rate: Start from 0.001

    Learning Rate Scheduler：StepLR(B4-> StepSize:5, B5-> StepSize:10), gamma=0.1

    TTA: TTA 10 times by following code
    test_transform = transforms.Compose([ transforms.RandomAffine(degrees=360), transforms.RandomHorizontalFlip(), transforms.RandomVerticalFlip(), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    Score:
    -> Public LB:
    B4 Classification: 0.821
    B5 Classification: 0.825
    B4 Regression:0.823
    B5 Regression:0.825
    -> Private LB
    B4 Classification: 0.919
    B5 Classification: 0.921
    B4 Regression: 0.917
    B5 Regression: 0.921

    Final Submission:
    Combining B4 & B5 regression output together. （Public LB:0.835, Private 0.925)
