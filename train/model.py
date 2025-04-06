import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights

class PokerCardClassifier(nn.Module):
    def __init__(self, num_classes=52):
        """
        Poker card classification model based on ResNet18.
        
        Args:
            num_classes: 52
        """
        super(PokerCardClassifier, self).__init__()
        self.backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        
        # Replace the final fully connected layer
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        
        self.pred_head = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        return self.pred_head(features)

def create_optimizer(model, memorization_lr=0.0003):
    """
    Create an optimizer specifically tuned for memorization.
    Uses different learning rates for backbone and memorization head.
    
    Args:
        model: The model to optimize
        memorization_lr: Learning rate for memorization head
        
    Returns:
        Optimizer configured for memorization
    """
    # Higher learning rate for the memorization head
    # Lower learning rate for the backbone
    params = [
        {'params': model.backbone.parameters(), 'lr': memorization_lr / 10},
        {'params': model.pred_head.parameters(), 'lr': memorization_lr}
    ]
    
    # Use Adam with zero weight decay to allow perfect memorization
    optimizer = torch.optim.Adam(params, weight_decay=0)
    
    return optimizer