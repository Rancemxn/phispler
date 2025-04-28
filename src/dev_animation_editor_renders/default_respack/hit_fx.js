function render(p) {
    const {
        ctx,
    } = this;

    ctx.canvas.style.backgroundColor = "black";

    const tfs = {
        linear: p => p,
        easeIn: (p, exp = 2) => p ** exp,
        easeOut: (p, exp = 2) => 1 - (1 - p) ** (exp + 2.5)
    }
    const fix_orp = p => p < 0 ? 0 : p > 1 ? 1 : p;

    const p_slower = fix_orp(p * 0.7);

    const circle = (x, y, r) => {
        ctx.beginPath();
        ctx.arc(x, y, r, 0, 2 * Math.PI);
    }

    const fillCircle = (x, y, r, a = 1.0) => {
        ctx.save();
        ctx.fillStyle = `rgba(255, 255, 255, ${a})`;
        circle(x, y, r);
        ctx.fill();
        ctx.restore();
    }

    const square = (x, y, s) => {
        ctx.beginPath();
        ctx.rect(x - s / 2, y - s / 2, s, s);
    }

    const strokeSquare = (x, y, s, lw, a = 1.0) => {
        ctx.save();
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth = lw;
        square(x, y, s);
        ctx.stroke();
        ctx.restore();
    }

    const rotatedSquare = (x, y, s, deg) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(deg * Math.PI / 180);
        square(0, 0, s);
        ctx.restore();
    }

    const strokeRotatedSquare = (x, y, s, deg, lw, a = 1.0) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(deg * Math.PI / 180);
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth = lw;
        rotatedSquare(0, 0, s);
        ctx.stroke();
        ctx.restore();
    }

    const arc = (x, y, r, start, dd) => {
        start *= Math.PI / 180;
        ctx.beginPath();
        ctx.arc(x, y, r, start, start + dd * Math.PI / 180);
    }

    const strokeArc = (x, y, r, start, dd, lw, a = 1.0) => {
        ctx.save();
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth = lw;
        arc(x, y, r, start, dd);
        ctx.stroke();
        ctx.restore();
    }

    const size = 256;
    const real_size = size;
    resizeCanvas(real_size, real_size);
    ctx.scale(real_size, real_size);

    ctx.translate(0.5, 0.5);
    ctx.scale(1.22, 1.22);
    ctx.translate(-0.5, -0.5);

    ctx.save();
    ctx.fillStyle = "white";

    const circ_1_size = (0.35 - 0.3 * tfs.easeOut(p, 2)) * 0.8;
    const circ_2_size = (0.3 - 0.1 * tfs.easeOut(fix_orp(p * 1.3), 2)) * 0.8;

    const square_1_size = (0.3 + 1.2 * tfs.easeOut(p_slower, 2)) * 0.82;
    const square_2_size = (0.3 + 1.0 * tfs.easeOut(p_slower, 2)) * 0.82;
    const square_2_lw = (0.13 - 0.125 * tfs.easeOut(p_slower, 5)) * 0.58;

    const arc_size = (0.2 + 0.3 * tfs.easeOut(p_slower, 2)) * 0.9;
    const arc_start = -135;
    const arc_dd = 45 * tfs.easeOut(p_slower, 2);
    const arc_lw = (0.005 + 0.015 * tfs.easeOut(p, 2)) * 0.8;

    strokeArc(
        0.5, 0.5,
        arc_size / 2,
        arc_start + arc_dd,
        90, arc_lw
    )

    strokeArc(
        0.5, 0.5,
        arc_size / 2,
        arc_start + arc_dd + 180,
        90, arc_lw
    )

    strokeSquare(0.5, 0.5, square_1_size / 2, 0.01 - 0.005 * tfs.easeOut(p, 2));
    strokeRotatedSquare(0.5, 0.5, square_2_size / 2, 45, square_2_lw, 0.7);
    fillCircle(0.5, 0.5, circ_2_size / 2, 0.3);
    fillCircle(0.5, 0.5, circ_1_size / 2);

    ctx.restore();

    const imgdata = ctx.getImageData(0, 0, real_size, real_size);
    const getindex = (x, y) => (y * real_size + x) * 4;

    for (let i = 0; i < real_size; i++) {
        for (let j = 0; j < real_size; j++) {
            const index = getindex(i, j);
            const r = imgdata.data[index];
            const g = imgdata.data[index + 1];
            const b = imgdata.data[index + 2];
            const a = imgdata.data[index + 3];

            const p_ = (i + 1) / real_size * (j + 1) / real_size;
            const x = 0.7 + 0.5 * p_;

            imgdata.data.set([
                r * x,
                g * x,
                b * x,
                a * (1.0 - tfs.easeIn(p, 1.3))
            ], index);
        }
    }

    ctx.putImageData(imgdata, 0, 0);
}