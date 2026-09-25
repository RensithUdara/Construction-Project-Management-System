(function () {
    const dataNode = document.getElementById('dashboard-chart-data');
    if (!dataNode) return;

    const data = JSON.parse(dataNode.textContent);
    const palette = ['#176b5f', '#d19a2a', '#3d6fb6', '#b85f40', '#6b7280', '#7c5a9b', '#2b8a3e', '#bd3f32'];

    function formatMoney(value) {
        if (value >= 1000000000) return `${(value / 1000000000).toFixed(1)}B`;
        if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
        return `${value}`;
    }

    function setup(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, rect.width, rect.height);
        ctx.font = '12px "Plus Jakarta Sans", system-ui, sans-serif';
        ctx.lineWidth = 1;
        return { ctx, width: rect.width, height: rect.height };
    }

    function drawEmpty(ctx, width, height) {
        ctx.fillStyle = '#667085';
        ctx.textAlign = 'center';
        ctx.fillText('No data available yet', width / 2, height / 2);
    }

    function barChart(canvasId, labels, series, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const { ctx, width, height } = setup(canvas);
        const max = Math.max(...series.flatMap(item => item.values), 0);
        if (!max) return drawEmpty(ctx, width, height);

        const left = 48;
        const right = 18;
        const top = 24;
        const bottom = 52;
        const chartW = width - left - right;
        const chartH = height - top - bottom;
        const groupW = chartW / labels.length;
        const barW = Math.max(8, (groupW - 18) / series.length);

        ctx.strokeStyle = '#e4e9ef';
        ctx.fillStyle = '#667085';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {
            const y = top + chartH - (chartH * i / 4);
            ctx.beginPath();
            ctx.moveTo(left, y);
            ctx.lineTo(width - right, y);
            ctx.stroke();
            const label = options.money ? formatMoney(max * i / 4) : Math.round(max * i / 4);
            ctx.fillText(label, left - 8, y + 4);
        }

        labels.forEach((label, index) => {
            const x = left + index * groupW + 10;
            series.forEach((item, sIndex) => {
                const value = item.values[index] || 0;
                const barH = chartH * value / max;
                ctx.fillStyle = item.color || palette[sIndex];
                ctx.fillRect(x + sIndex * barW, top + chartH - barH, barW - 2, barH);
            });
            ctx.save();
            ctx.translate(x + groupW / 2 - 8, height - 18);
            ctx.rotate(-0.38);
            ctx.fillStyle = '#667085';
            ctx.textAlign = 'right';
            ctx.fillText(label.slice(0, 16), 0, 0);
            ctx.restore();
        });

        let legendX = left;
        series.forEach((item, index) => {
            ctx.fillStyle = item.color || palette[index];
            ctx.fillRect(legendX, 6, 10, 10);
            ctx.fillStyle = '#344054';
            ctx.textAlign = 'left';
            ctx.fillText(item.name, legendX + 15, 15);
            legendX += item.name.length * 7 + 36;
        });
    }

    function doughnutChart(canvasId, labels, values) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const { ctx, width, height } = setup(canvas);
        const total = values.reduce((sum, value) => sum + value, 0);
        if (!total) return drawEmpty(ctx, width, height);

        const cx = width / 2;
        const cy = height / 2 - 12;
        const radius = Math.min(width, height) / 3.3;
        let start = -Math.PI / 2;

        values.forEach((value, index) => {
            const angle = value / total * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, radius, start, start + angle);
            ctx.closePath();
            ctx.fillStyle = palette[index % palette.length];
            ctx.fill();
            start += angle;
        });

        ctx.beginPath();
        ctx.arc(cx, cy, radius * 0.58, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.fillStyle = '#18202a';
        ctx.textAlign = 'center';
        ctx.font = '700 24px "Space Grotesk", system-ui, sans-serif';
        ctx.fillText(total, cx, cy + 8);

        ctx.font = '12px "Plus Jakarta Sans", system-ui, sans-serif';
        labels.forEach((label, index) => {
            const x = 18 + (index % 2) * (width / 2);
            const y = height - 52 + Math.floor(index / 2) * 18;
            ctx.fillStyle = palette[index % palette.length];
            ctx.fillRect(x, y, 9, 9);
            ctx.fillStyle = '#344054';
            ctx.textAlign = 'left';
            ctx.fillText(`${label}: ${values[index]}`, x + 14, y + 9);
        });
    }

    function horizontalBars(canvasId, rows, suffix = '') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const { ctx, width, height } = setup(canvas);
        if (!rows.length) return drawEmpty(ctx, width, height);

        const max = Math.max(...rows.map(row => row.value), 1);
        const left = 84;
        const top = 20;
        const rowH = Math.min(34, (height - 30) / rows.length);
        rows.forEach((row, index) => {
            const y = top + index * rowH;
            const barW = (width - left - 42) * row.value / max;
            ctx.fillStyle = '#eef3f4';
            ctx.fillRect(left, y, width - left - 34, 14);
            ctx.fillStyle = palette[index % palette.length];
            ctx.fillRect(left, y, barW, 14);
            ctx.fillStyle = '#344054';
            ctx.textAlign = 'right';
            ctx.fillText(row.label, left - 10, y + 12);
            ctx.textAlign = 'left';
            ctx.fillText(`${row.value}${suffix}`, left + barW + 8, y + 12);
        });
    }

    function render() {
        barChart('budgetChart', data.budget.labels, [
            { name: 'Budget', values: data.budget.budget, color: '#176b5f' },
            { name: 'Actual', values: data.budget.actual, color: '#d19a2a' },
            { name: 'Committed', values: data.budget.committed, color: '#3d6fb6' },
        ], { money: true });
        doughnutChart('statusChart', data.projectStatus.labels, data.projectStatus.values);
        horizontalBars('progressChart', data.projectProgress, '%');
        doughnutChart('workflowChart', data.workflow.labels, data.workflow.values);
    }

    render();
    window.addEventListener('resize', render);
})();
