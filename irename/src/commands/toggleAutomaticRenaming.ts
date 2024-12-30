import * as vscode from 'vscode';

export async function toggleAutomaticRenaming() {
    const config = vscode.workspace.getConfiguration('irename');
    const currentValue = config.get<boolean>('automaticRenaming', false); // Default to false
    await config.update('automaticRenaming', !currentValue, vscode.ConfigurationTarget.Global);
    vscode.window.showInformationMessage(`Automatic renaming is now ${!currentValue ? 'enabled' : 'disabled'}`);
}