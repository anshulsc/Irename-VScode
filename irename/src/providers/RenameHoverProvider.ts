import * as vscode from 'vscode';
import { apiClient } from '../utils/apiClient';

export class RenameHoverProvider implements vscode.HoverProvider {
    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        const config = vscode.workspace.getConfiguration('renameit');
        const isAutomaticRenamingEnabled = config.get<boolean>('automaticRenaming', false);

        if (!isAutomaticRenamingEnabled) {
            return null;
        }

        const identifierRange = document.getWordRangeAtPosition(position);
        if (!identifierRange) {
            return null;
        }

        const line = identifierRange.start.line;
        const char = identifierRange.start.character;
        const code = document.getText();
        const num_tokens = -1; // Automatic mode

        try {
            const response = await apiClient.post('/rename/', { code, line, char, num_tokens });
            const suggestions: string[] = response.data.suggestions;
            const probabilities: number[] = response.data.probabilities;

            if (suggestions.length === 0) {
                return null;
            }

            // Create Markdown content for the hover
            let hoverContent = new vscode.MarkdownString();
            hoverContent.appendMarkdown('**ReNameIt Suggestions:**\n\n');
            suggestions.forEach((suggestion, index) => {
                hoverContent.appendMarkdown(`- ${suggestion} (Probability: ${probabilities[index].toFixed(2)})\n`);
            });

            return new vscode.Hover(hoverContent);
        } catch (error) {
            console.error('Error fetching suggestions for hover:', error);
            return null;
        }
    }
}