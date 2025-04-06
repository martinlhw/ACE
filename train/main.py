import os
import argparse
import torch
import matplotlib.pyplot as plt
from model import PokerCardClassifier, create_optimizer
from data import create_data_loaders
from train import train
from eval import evaluate_model, plot_confusion_matrix

def parse_args():
    parser = argparse.ArgumentParser(description='train and eval')
    parser.add_argument('--data_dir', type=str, required=True, help='dir with single card images')
    parser.add_argument('--output_dir', type=str, default='output', help='output directory')
    parser.add_argument('--batch_size', type=int, default=16, help='batch size for training')
    parser.add_argument('--num_epochs', type=int, default=100, help='# of training epochs')
    parser.add_argument('--repetitions', type=int, default=100, help='# of repetitions per image')
    parser.add_argument('--eval_only', action='store_true', help='Only run evaluation')
    parser.add_argument('--model_path', type=str, help='Path to trained model for evaluation')
    
    return parser.parse_args()

def main(args):
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create directories
    os.makedirs(args.output_dir, exist_ok=True)
    checkpoint_dir = os.path.join(args.output_dir, 'checkpoints')
    results_dir = os.path.join(args.output_dir, 'results')
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    print("creating data loaders from single images...")
    train_loader, val_loader, test_loader, class_names = create_data_loaders(
        args.data_dir, 
        batch_size=args.batch_size, 
        repetitions=args.repetitions
    )
    
    # create or load model
    if args.eval_only and args.model_path:
        print(f"Loading model from {args.model_path}...")
        checkpoint = torch.load(args.model_path)
        model = PokerCardClassifier(num_classes=len(class_names))
        model.load_state_dict(checkpoint['model_state_dict'])
        model = model.to(device)
    else:
        print("Creating a new model...")
        model = PokerCardClassifier(num_classes=len(class_names)).to(device)
        
        optimizer = create_optimizer(model)
        
        # Train the model to memorize the cards
        print("Training model to memorize cards...")
        model, result = train(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            optimizer=optimizer,
            num_epochs=args.num_epochs,
            device=device,
            checkpoint_dir=checkpoint_dir
        )
        
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(result['train_loss'], label='Training Loss')
        plt.plot(result['val_loss'], label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.title('Training and Validation Loss')
        
        plt.subplot(1, 2, 2)
        plt.plot(result['train_acc'], label='Training Accuracy')
        plt.plot(result['val_acc'], label='Validation Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy (%)')
        plt.legend()
        plt.title('Training and Validation Accuracy')
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'res.png'))
    
    # Evaluate the model
    print("Evaluating model...")
    test_acc, all_preds, all_labels = evaluate_model(model, test_loader, device=device)
    
    # Plot confusion matrix
    plot_confusion_matrix(
        all_preds, 
        all_labels, 
        class_names, 
        figsize=(15, 15), 
        save_path=os.path.join(results_dir, 'memorization_confusion_matrix.png')
    )
    
    print(f"Test accuracy: {test_acc:.2f}%")

if __name__ == '__main__':
    args = parse_args()
    main(args)