import * as vscode from 'vscode';
import axios from 'axios';
import { renameIdentifier } from './commands/renameIdentifier';
import { RenameCodeActionProvider } from './providers/RenameCodeActionProvider';
import { toggleAutomaticRenaming } from './commands/toggleAutomaticRenaming';
import { RenameHoverProvider } from './providers/RenameHoverProvider';


export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "renameit" is now active!');

    let disposable = vscode.commands.registerCommand('irename.ping', async () => {
        try {
            const response = await axios.get('http://127.0.0.1:8000/');
            vscode.window.showInformationMessage(response.data.message);
        } catch (error) {
            vscode.window.showErrorMessage('Error connecting to server.');
        }
    });

    context.subscriptions.push(disposable);

    context.subscriptions.push(
        vscode.commands.registerCommand('irename.renameIdentifier', (uri, line, char) => {
            renameIdentifier(uri, line, char, -1); // -1 for automatic mode
        })
    );
    
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider('java', new RenameCodeActionProvider(), {
            providedCodeActionKinds: RenameCodeActionProvider.providedCodeActionKinds
        })
    );


     // Register the command to toggle automatic renaming
     context.subscriptions.push(
        vscode.commands.registerCommand('irename.toggleAutomaticRenaming', toggleAutomaticRenaming)
    );

    // Register the Hover provider for Java files
    context.subscriptions.push(
        vscode.languages.registerHoverProvider('java', new RenameHoverProvider())
    );

}

export function deactivate() {} 