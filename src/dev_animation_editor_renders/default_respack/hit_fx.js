function render(p) {
    const {
        ctx,
    } = this;

    const tfs = {
        linear: p => p,
        easeIn: p => p * p,
        easeOut: p => p * (2 - p),
        easeInOut: p => p < 0.5 ? 2 * p * p : -1 + (4 - 2 * p) * p,
    }

    const fix_orp = p => p < 0 ? 0 : p > 1 ? 1 : p;

    const scale = this.note_draw_render_scale;
    
    const size = 512;
    resizeCanvas(size * scale, size * scale);
    ctx.scale(scale, scale);

    ctx.save();
    ctx.fillStyle = "white";

    ctx.restore();
}