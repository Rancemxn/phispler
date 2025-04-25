function render() {
    const {
        ctx,
        note_deg
    } = this;
    
    const scale = this.note_draw_render_scale / 4;
    const flick_deg = this.note_render_flick_deg;
    const flick_rad = flick_deg * Math.PI / 180;

    const get_dpower = (w, h) => this.get_dpower(w, h, note_deg);
    const get_dpower_flick = (w, h) => this.get_dpower(w, h, flick_deg);

    const [w, h] = [989, 200];
    const fh = h / 2;
    resizeCanvas(w * scale, h * scale);
    ctx.scale(scale, scale);

    ctx.save();
    ctx.translate(0, h / 4);

    const lr_bar_width = 24;
    const lr_bar_item_height = fh / 2;
    const lr_bar_dpower = get_dpower(lr_bar_width, lr_bar_item_height);
    const lr_bar_dpower_width = lr_bar_dpower * lr_bar_width;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(lr_bar_dpower_width, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width - lr_bar_dpower_width, fh / 2);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width, fh);
    ctx.lineTo(lr_bar_dpower_width, fh);
    ctx.lineTo(0, fh / 2);
    ctx.lineTo(lr_bar_dpower_width, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(w - lr_bar_dpower_width, 0);
    ctx.lineTo(w, fh / 2);
    ctx.lineTo(w - lr_bar_dpower_width, fh);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width, fh);
    ctx.lineTo(w - lr_bar_width, fh / 2);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width, 0);
    ctx.lineTo(w - lr_bar_dpower_width, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    const main_padx = 25;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(lr_bar_dpower_width + lr_bar_width + main_padx, 0);
    ctx.lineTo(lr_bar_width + main_padx, fh / 2);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width + main_padx, fh);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width - main_padx, fh);
    ctx.lineTo(w - lr_bar_width - main_padx, fh / 2);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width - main_padx, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width + main_padx, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    const inner_padx = 36;
    const inner_pady = 25;
    const inner_dpower_x = (fh - inner_pady * 2) / fh;
    const pink_bar_width = 315;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo((lr_bar_dpower_width * inner_dpower_x) + lr_bar_width + main_padx + inner_padx, inner_pady);
    ctx.lineTo(lr_bar_width + main_padx + inner_padx, fh / 2);
    ctx.lineTo((lr_bar_dpower_width * inner_dpower_x) + lr_bar_width + main_padx + inner_padx, fh - inner_pady);
    ctx.lineTo(lr_bar_width + main_padx + inner_padx + pink_bar_width, fh - inner_pady);
    ctx.lineTo(lr_bar_width + main_padx + inner_padx + pink_bar_width, inner_pady);
    ctx.lineTo((lr_bar_dpower_width * inner_dpower_x) + lr_bar_width + main_padx + inner_padx, inner_pady);
    ctx.fillStyle = `rgb(${0xfe}, ${0x43}, ${0x65})`;
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(w - (lr_bar_dpower_width * inner_dpower_x) - lr_bar_width - main_padx - inner_padx, fh - inner_pady);
    ctx.lineTo(w - lr_bar_width - main_padx - inner_padx, fh / 2);
    ctx.lineTo(w - (lr_bar_dpower_width * inner_dpower_x) - lr_bar_width - main_padx - inner_padx, inner_pady);
    ctx.lineTo(w - lr_bar_width - main_padx - inner_padx - pink_bar_width, inner_pady);
    ctx.lineTo(w - lr_bar_width - main_padx - inner_padx - pink_bar_width, fh - inner_pady);
    ctx.lineTo(w - (lr_bar_dpower_width * inner_dpower_x) - lr_bar_width - main_padx - inner_padx, fh - inner_pady);
    ctx.fillStyle = `rgb(${0xfe}, ${0x43}, ${0x65})`;
    ctx.fill();
    ctx.restore();

    ctx.restore();

    const mn_left = 473;
    const mn_right = 515;
    const mn_dx = 40;
    const mn_height = 125;
    const mn_clean_size = 12;

    const mn_plot = [
        [mn_left, 0],
        [mn_left, mn_height],
        [mn_left - mn_dx, mn_height - Math.tan(flick_rad) * mn_dx],
        [mn_left - mn_dx, mn_height - Math.tan(flick_rad) * mn_dx + (h - mn_height - Math.tan(flick_rad) * (mn_right - mn_left))],
        [mn_right, h],
        [mn_right, h - mn_height],
        [mn_right + mn_dx, h - mn_height + Math.tan(flick_rad) * mn_dx],
        [mn_right + mn_dx, h - mn_height + Math.tan(flick_rad) * mn_dx - (h - mn_height - Math.tan(flick_rad) * (mn_right - mn_left))]
    ];

    const rect_mn_plot = () => {
        ctx.beginPath();
        ctx.moveTo(...mn_plot[0]);
        for (let i = 1; i < mn_plot.length; i++) {
            ctx.lineTo(...mn_plot[i]);
        }
        ctx.lineTo(...mn_plot[0]);
    }

    ctx.save();
    rect_mn_plot();
    ctx.fillStyle = "blue";
    ctx.fill();
    ctx.restore();
}