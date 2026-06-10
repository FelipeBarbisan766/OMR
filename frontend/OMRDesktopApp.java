import java.awt.BorderLayout;
import java.awt.GridLayout;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

public class OMRDesktopApp {
    private static final String BASE_URL = "http://127.0.0.1:5000";
    private final HttpClient client = HttpClient.newHttpClient();

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new OMRDesktopApp().buildUI());
    }

    private void buildUI() {
        JFrame frame = new JFrame("OMR Local (Java)");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(700, 500);

        JTextField studentIdField = new JTextField("ALUNO-001");
        JTextField questionsField = new JTextField("10");
        JTextField imagePathField = new JTextField();
        JTextArea output = new JTextArea("Pronto.");
        output.setEditable(false);

        JButton generateButton = new JButton("Gerar gabarito (PDF)");
        generateButton.addActionListener(event -> {
            String json = String.format(
                "{\"student_id\":\"%s\",\"num_questions\":%s}",
                studentIdField.getText().trim(),
                questionsField.getText().trim()
            );
            sendJson("/api/generate-sheet", json, output);
        });

        JButton browseButton = new JButton("Selecionar imagem");
        browseButton.addActionListener(event -> {
            JFileChooser chooser = new JFileChooser();
            if (chooser.showOpenDialog(frame) == JFileChooser.APPROVE_OPTION) {
                imagePathField.setText(chooser.getSelectedFile().getAbsolutePath());
            }
        });

        JButton processButton = new JButton("Detectar respostas");
        processButton.addActionListener(event -> {
            File imageFile = new File(imagePathField.getText().trim());
            if (!imageFile.exists()) {
                output.setText("{\"error\":\"Selecione uma imagem válida.\"}");
                return;
            }
            sendMultipart("/api/process-image", imageFile, questionsField.getText().trim(), output);
        });

        JPanel fields = new JPanel(new GridLayout(0, 2, 8, 8));
        fields.add(new JLabel("ID do aluno"));
        fields.add(studentIdField);
        fields.add(new JLabel("Questões"));
        fields.add(questionsField);
        fields.add(new JLabel("Imagem (foto/scan)"));
        fields.add(imagePathField);

        JPanel buttons = new JPanel(new GridLayout(1, 3, 8, 8));
        buttons.add(generateButton);
        buttons.add(browseButton);
        buttons.add(processButton);

        JPanel top = new JPanel(new BorderLayout(8, 8));
        top.add(fields, BorderLayout.CENTER);
        top.add(buttons, BorderLayout.SOUTH);

        frame.getContentPane().setLayout(new BorderLayout(8, 8));
        frame.getContentPane().add(top, BorderLayout.NORTH);
        frame.getContentPane().add(new JScrollPane(output), BorderLayout.CENTER);
        frame.setVisible(true);
    }

    private void sendJson(String path, String json, JTextArea output) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + path))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            output.setText(response.body());
        } catch (Exception e) {
            output.setText("{\"error\":\"Falha ao chamar API: " + e.getMessage() + "\"}");
        }
    }

    private void sendMultipart(String path, File imageFile, String numQuestions, JTextArea output) {
        String boundary = "----OMRBoundary" + System.currentTimeMillis();
        try {
            byte[] body = buildMultipartBody(boundary, imageFile, numQuestions);
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + path))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(body))
                .build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            output.setText(response.body());
        } catch (Exception e) {
            output.setText("{\"error\":\"Falha ao enviar imagem: " + e.getMessage() + "\"}");
        }
    }

    private byte[] buildMultipartBody(String boundary, File imageFile, String numQuestions) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        String lineBreak = "\r\n";

        out.write(("--" + boundary + lineBreak).getBytes(StandardCharsets.UTF_8));
        out.write(("Content-Disposition: form-data; name=\"num_questions\"" + lineBreak + lineBreak)
            .getBytes(StandardCharsets.UTF_8));
        out.write(numQuestions.getBytes(StandardCharsets.UTF_8));
        out.write(lineBreak.getBytes(StandardCharsets.UTF_8));

        out.write(("--" + boundary + lineBreak).getBytes(StandardCharsets.UTF_8));
        out.write(("Content-Disposition: form-data; name=\"image\"; filename=\"" + imageFile.getName() + "\""
            + lineBreak).getBytes(StandardCharsets.UTF_8));
        out.write(("Content-Type: application/octet-stream" + lineBreak + lineBreak).getBytes(StandardCharsets.UTF_8));
        out.write(Files.readAllBytes(imageFile.toPath()));
        out.write(lineBreak.getBytes(StandardCharsets.UTF_8));

        out.write(("--" + boundary + "--" + lineBreak).getBytes(StandardCharsets.UTF_8));
        return out.toByteArray();
    }
}
