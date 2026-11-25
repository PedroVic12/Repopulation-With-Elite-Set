// frontend/src/components/Chart.js
import React from 'react';
import { Box } from '@mui/material';

const Chart = ({ chartData }) => {
    return (
        <Box>
            <img src={`data:image/png;base64,${chartData}`} alt="Chart" />
        </Box>
    );
};

export default Chart;
