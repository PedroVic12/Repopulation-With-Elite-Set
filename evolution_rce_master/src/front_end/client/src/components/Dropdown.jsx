// frontend/src/components/Dropdown.js
import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

const Dropdown = ({ chartType, onChartTypeChange }) => {
    return (
        <FormControl fullWidth>
            <InputLabel>Chart Type</InputLabel>
            <Select
                value={chartType}
                onChange={(e) => onChartTypeChange(e.target.value)}
            >
                <MenuItem value="bar">Bar Chart</MenuItem>
                <MenuItem value="line">Line Chart</MenuItem>
                <MenuItem value="scatter">Scatter Chart</MenuItem>
            </Select>
        </FormControl>
    );
};

export default Dropdown;
