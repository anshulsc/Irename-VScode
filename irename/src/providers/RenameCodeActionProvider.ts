import * as vscode from 'vscode';
import { renameIdentifier } from '../commands/renameIdentifier';

export class RenameCodeActionProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.RefactorRewrite
    ];

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<(vscode.CodeAction | vscode.Command)[]> {
        // Check if the selected range is an identifier
        const identifierRange = document.getWordRangeAtPosition(range.start);
        if (!identifierRange) {
            return [];
        }

        // Create a CodeAction to trigger the renaming command
        const codeAction = new vscode.CodeAction('Rename Identifier (ReNameIt)', vscode.CodeActionKind.RefactorRewrite);
        codeAction.command = {
            command: 'irename.renameIdentifier',
            title: 'Rename Identifier',
            arguments: [document.uri, identifierRange.start.line + 1, identifierRange.start.character + 1, -1], // -1 for automatic mode
        };

        return [codeAction];
    }
}