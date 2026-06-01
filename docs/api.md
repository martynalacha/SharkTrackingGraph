# Specyfikacja API

Poniżej znajduje się interaktywna specyfikacja endpointów REST API wygenerowana automatycznie z kodu źródłowego aplikacji.

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>

<div id="swagger-ui"></div>

<script>
  window.onload = () => {
    window.ui = SwaggerUIBundle({
      url: '../openapi.json',
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.currentPreset
      ]
    });
  };
</script>
