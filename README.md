# sd-webui-keyframer
Automatic1111 Stable Diffusion WebUI extension, increase consistency between images by generating in same latent space.

Beta. Script accepts multiple images, plots them on a grid, generates against them, then splits them up again.

- Adjust rows and columns until image is most square and within size limits you can handle.
- Set max dimensions to constrain generated sheet within your known limits.
- Press "generate sheet." Image will populate.
   - Empty spaces in grid will be populated with repeats (black space ruins generation).
- Press "generate" in img2img. Images will be sent to default directory.
