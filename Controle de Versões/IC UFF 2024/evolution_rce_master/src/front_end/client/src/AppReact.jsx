import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import DataTable from './components/DataTable';
import { Container, MenuItem, Select, Typography, Box } from '@mui/material';

const App = () => {
    const [chartType, setChartType] = useState('Bar Chart');
    const [chartData, setChartData] = useState(null);
    const [insights, setInsights] = useState('');
    const [tableData, setTableData] = useState([]);
    const [columnDefs, setColumnDefs] = useState([
        { headerName: 'Year', field: 'Year' },
        { headerName: 'Annual number of AI systems by domain', field: 'Annual number of AI systems by domain' },
        { headerName: 'Entity', field: 'Entity' },
    ]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('http://localhost:8050/update_graph', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ chartType }),
                });

                const data = await response.json();
                setChartData(data.figure);
                setInsights(data.insights);
                setTableData(data.tableData); // Assumindo que a resposta inclui dados da tabela
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, [chartType]);

    return (
        <Container>
            <Typography variant="h1">Interactive Data Visualization</Typography>
            <Select
                value={chartType}
                onChange={(e) => setChartType(e.target.value)}
            >
                <MenuItem value="Bar Chart">Bar Chart</MenuItem>
                <MenuItem value="Line Chart">Line Chart</MenuItem>
                <MenuItem value="Scatter Chart">Scatter Chart</MenuItem>
            </Select>
            {chartData && (
                <Plot
                    data={chartData.data}
                    layout={chartData.layout}
                    config={chartData.config}
                />
            )}
            <Box>{insights}</Box>
            <DataTable rowData={tableData} columnDefs={columnDefs} />
        </Container>
    );
};

export default App;
