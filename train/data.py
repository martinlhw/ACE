import os
import random
import shutil
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

torch.manual_seed(42)
random.seed(42)
np.random.seed(42)

class PokerCardDataset(Dataset):
    def __init__(self, data_dir, transform=None, repetitions=100):
        """
        Args:
            data_dir: Directory containing image per class
            transform: Transforms to apply
            repetitions: Number of times to repeat each image
        """
        self.data_dir = data_dir
        self.transform = transform
        self.repetitions = repetitions
        
        self.classes = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        
        # For each class, find one image
        self.samples = []
        for class_name in self.classes:
            class_dir = os.path.join(data_dir, class_name)
            
            # Find the first valid image
            for img_name in os.listdir(class_dir):
                if img_name.endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(class_dir, img_name)
                    label = self.class_to_idx[class_name]
                    
                    # Add this image to samples multiple times
                    for _ in range(repetitions):
                        self.samples.append((img_path, label))
                    
                    # Only use the first image in each class
                    break
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        img = Image.open(img_path).convert('RGB')
        
        if self.transform:
            img = self.transform(img)
            
        return img, label

def get_transforms(use_augmentation=False):
    """
    https://pytorch.org/vision/main/auto_examples/transforms/plot_transforms_illustrations.html#sphx-glr-auto-examples-transforms-plot-transforms-illustrations-py
    Define transforms for training and testing.
    
    Args:
        use_augmentation: Whether to use data augmentation for training
    
    Returns:
        train_transform: Transforms for training data
        test_transform: Transforms for validation/test data
    """
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ColorJitter(brightness=0.05, contrast=0.05, saturation=0, hue=0),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, test_transform

def create_datasets(data_dir, repetitions=100):
    """
    Create datasets for training with a single image per class.
    
    Args:
        data_dir: Directory containing original card images (one per class)
        repetitions: Number of times to repeat each image
        
    Returns:
        train_dataset: Dataset for training
        val_dataset: Dataset for validation
        test_dataset: Dataset for testing
        class_names: List of class names
    """
    train_transform, test_transform = get_transforms()
    
    # Create the datasets
    train_dataset = PokerCardDataset(data_dir, transform=train_transform, repetitions=repetitions)
    
    # For validation and test, we use the same single image per class, but with different transforms
    val_dataset = PokerCardDataset(data_dir, transform=test_transform, repetitions=10)
    test_dataset = PokerCardDataset(data_dir, transform=test_transform, repetitions=10)
    
    return train_dataset, val_dataset, test_dataset, train_dataset.classes

def create_data_loaders(data_dir, batch_size=32, repetitions=100):
    """
    Create data loaders
    
    Args:
        data_dir: Directory containing original card images (one per class)
        batch_size: Batch size
        repetitions: Number of times to repeat each image
        
    Returns:
        train_loader: DataLoader for training
        val_loader: DataLoader for validation
        test_loader: DataLoader for testing
        class_names: List of class names
    """
    train_dataset, val_dataset, test_dataset, class_names = create_datasets(
        data_dir, repetitions=repetitions
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    return train_loader, val_loader, test_loader, class_names