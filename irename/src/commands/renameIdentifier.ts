import * as vscode from 'vscode';
import axios from 'axios';

export async function renameIdentifier(uri: vscode.Uri, line: number, char: number, num_tokens: number) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor found.');
        return;
    }

    const document = editor.document;
    const code = document.getText();

    try {
        const response = await axios.post('http://127.0.0.1:8000/rename/', { code, line, char, num_tokens });
        const suggestions: string[] = response.data.suggestions;
        const probabilities: number[] = response.data.probabilities;

        // Combine suggestions and probabilities for display
        const items = suggestions.map((suggestion, index) => ({
            label: suggestion,
            description: `Probability: ${probabilities[index].toFixed(2)}`
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a new name for the identifier',
        });

        if (selected) {
            const selectedSuggestion = selected.label;

            // print the selected suggestion
            console.log(selectedSuggestion);

            const occurrences = findOccurrencesInDocument(document, line, char);
            // Apply the selected suggestion
            await editor.edit(editBuilder => {
                for (const occurrence of occurrences) {
                    editBuilder.replace(occurrence, selectedSuggestion);
                }
            });
        }
    } catch (error) {
        if (axios.isAxiosError(error)) {
            // Handle Axios specific errors (e.g., network errors, timeouts)
            console.error('Axios error:', error.message);
            if (error.response) {
                // Server responded with a status code outside of 2xx range
                console.error('Error status:', error.response.status);
                console.error('Error data:', error.response.data);
                vscode.window.showErrorMessage(`Server error: ${error.response.status} - ${JSON.stringify(error.response.data)}`);
            } else if (error.request) {
                // Request was made but no response was received
                console.error('No response received for the request');
                vscode.window.showErrorMessage('No response received from server.');
            } else {
                // Error setting up the request
                console.error('Error setting up the request:', error.message);
                vscode.window.showErrorMessage('Error setting up the request.');
            }
        } else {
            // Handle other types of errors
            console.error('An unexpected error occurred:', error);
            vscode.window.showErrorMessage('An unexpected error occurred.');
        }
    }
}

function findOccurrencesInDocument(document: vscode.TextDocument, line: number, char: number): vscode.Range[] {
    const occurrences: vscode.Range[] = [];
    const targetLine = document.lineAt(line - 1);
    const wordRange = document.getWordRangeAtPosition(new vscode.Position(line - 1, char - 1));

    if (!wordRange || wordRange.isEmpty) {
        return occurrences;
    }

    
    const targetWord = document.getText(wordRange);
    console.log(targetWord);

    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        let index = line.text.indexOf(targetWord);

        while (index !== -1) {
            const start = new vscode.Position(i, index);
            const end = new vscode.Position(i, index + targetWord.length);
            const range = new vscode.Range(start, end);

            // Check if the found word is the same as the target word at the specified position
            const isSameWord = document.getText(range) === targetWord;
            const isSamePosition = (i === line.lineNumber && index === wordRange.start.character);

            if (isSameWord && isSamePosition) {
                occurrences.push(range);
            } else if (isSameWord && !isSamePosition){
                occurrences.push(range);
            }

            index = line.text.indexOf(targetWord, index + targetWord.length);
        }
    }

    return occurrences;
}