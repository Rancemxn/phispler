function render() {
    const {
        ctx,
        note_deg
    } = this;
    
    const scale = this.note_draw_render_scale / 2;
    const flick_deg = this.note_render_flick_deg;
    const flick_rad = flick_deg * Math.PI / 180;
    const flick_color = `rgb(${0xfe}, ${0x43}, ${0x65})`;

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
    ctx.fillStyle = flick_color;
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
    ctx.fillStyle = flick_color;
    ctx.fill();
    ctx.restore();

    const mn_left = 473;
    const mn_right = 515;
    const mn_dx = 40;
    const mn_height = 125;
    const mn_clean_size = 12;

    const mn_small_dy = (h - mn_height - Math.tan(flick_rad) * (mn_right - mn_left));
    const mn_clean_small_dy = fh - mn_small_dy - mn_clean_size;

    const mn_plot = [
        [mn_left, 0],
        [mn_left, mn_height],
        [mn_left - mn_dx, mn_height - Math.tan(flick_rad) * mn_dx],
        [mn_left - mn_dx, mn_height - Math.tan(flick_rad) * mn_dx + mn_small_dy],
        [mn_right, h],
        [mn_right, h - mn_height],
        [mn_right + mn_dx, h - mn_height + Math.tan(flick_rad) * mn_dx],
        [mn_right + mn_dx, h - mn_height + Math.tan(flick_rad) * mn_dx - mn_small_dy]
    ];

    const mn_clean_plot = [
        [mn_left - mn_clean_size, 0],
        [mn_left - mn_clean_size, mn_clean_small_dy + mn_clean_size],
        [mn_left - mn_dx - mn_clean_size, mn_clean_small_dy + mn_clean_size - Math.tan(flick_rad) * mn_dx],
        [mn_left - mn_dx - mn_clean_size, fh],
        [mn_right + mn_clean_size, fh],
        [mn_right + mn_clean_size, fh - mn_clean_small_dy - mn_clean_size],
        [mn_right + mn_dx + mn_clean_size, fh - mn_clean_small_dy - mn_clean_size + Math.tan(flick_rad) * mn_dx],
        [mn_right + mn_dx + mn_clean_size, 0]
    ];

    const inner_color_fill_padx = 24;
    const inner_color_fill_pady = 40;
    const inner_color_fill_tr_size = 35;
    const inner_color_fill_clip_circ_size = 24;

    const inner_color_fill_polts = [
        [
            [mn_left + inner_color_fill_padx, inner_color_fill_pady],
            [mn_left + inner_color_fill_padx, inner_color_fill_pady + inner_color_fill_tr_size],
            [mn_left + inner_color_fill_padx + Math.cos(flick_rad) * inner_color_fill_tr_size, inner_color_fill_pady + Math.sin(flick_rad) * inner_color_fill_tr_size],
        ],
        [
            [mn_right - inner_color_fill_padx, h - inner_color_fill_pady],
            [mn_right - inner_color_fill_padx, h - inner_color_fill_pady - inner_color_fill_tr_size],
            [mn_right - inner_color_fill_padx - Math.cos(flick_rad) * inner_color_fill_tr_size, h - inner_color_fill_pady - Math.sin(flick_rad) * inner_color_fill_tr_size],
        ]
    ];

    const rect_mn_plot = plot => {
        ctx.beginPath();
        ctx.moveTo(...plot[0]);
        for (let i = 1; i < plot.length; i++) {
            ctx.lineTo(...plot[i]);
        }
        ctx.lineTo(...plot[0]);
    }

    const draw_circlr = (x, y, r, fill_color, start_deg, end_deg) => {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.arc(x, y, r, start_deg * Math.PI / 180, end_deg * Math.PI / 180);
        ctx.lineTo(x, y);
        ctx.fillStyle = fill_color;
        ctx.fill();
        ctx.restore();
    }
    
    ctx.save();
    rect_mn_plot(mn_clean_plot);
    ctx.globalCompositeOperation = "destination-out";
    ctx.fill();
    ctx.restore();

    ctx.restore();

    ctx.save();
    rect_mn_plot(mn_plot);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    for (const plot of inner_color_fill_polts) {
        ctx.save();
        rect_mn_plot(plot);
        ctx.fillStyle = flick_color;
        ctx.fill();
        ctx.restore();
    }

    draw_circlr(mn_left, mn_height, inner_color_fill_clip_circ_size, "white", 0, 90 + flick_deg * 2);
    draw_circlr(mn_right, h - mn_height, inner_color_fill_clip_circ_size, "white", -180, -90 + flick_deg * 2);
}